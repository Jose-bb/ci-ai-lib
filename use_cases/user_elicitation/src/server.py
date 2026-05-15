from pydantic import BaseModel, Field
from fastmcp import FastMCP, Context

# Initialize the FastMCP server
server = FastMCP("ActionConfirmationServer")

class ConfirmationResponse(BaseModel):
    """Schema for the expected user response during elicitation."""
    is_confirmed: bool = Field(
        ..., 
        description="Whether the user confirms the action (True) or not (False)."
    )
    reason: str = Field(
        default="No reason provided", 
        description="Optional reason for the decision."
    )

@server.tool()
async def deploy_pytorch_model(model_name: str, target_environment: str, ctx: Context) -> str:
    """
    Simulates deploying a serialized PyTorch model to a target environment.
    Requires explicit human confirmation via elicitation before proceeding.
    
    Args:
        model_name: The name of the PyTorch model to deploy.
        target_environment: The environment (e.g., 'production', 'staging').
        ctx: The FastMCP Context object used to trigger elicitation.
    """
    elicitation_message = (
        f"DEPLOYMENT AUTHORIZATION: The agent is attempting to deploy the PyTorch model "
        f"'{model_name}' to the '{target_environment}' environment. "
        f"Do you explicitly approve this action?"
    )
    
    # Trigger elicitation
    user_input = await ctx.elicit(
        elicitation_message,
        response_type=ConfirmationResponse
    )
    
    # Handle the user's response
    if not user_input:
        return f"Operation aborted: User cancelled the deployment of '{model_name}'."
    
    # Safely extract the Pydantic model from the AcceptedElicitation wrapper
    if hasattr(user_input, 'content'):
        response_data = user_input.content
    elif hasattr(user_input, 'data'):
        response_data = user_input.data
    else:
        print(f"\n[SERVER DEBUG] Unknown wrapper structure. Attributes: {dir(user_input)}\n")
        return f"Internal Error: Could not extract payload from {type(user_input).__name__}."
    
    # Now we safely use the extracted Pydantic model
    if not response_data.is_confirmed:
        return f"Operation blocked: User denied the deployment. Reason: {response_data.reason}"
        
    return f"Success: PyTorch model '{model_name}' is successfully deploying to '{target_environment}'. User authorization reason: {response_data.reason}"

if __name__ == "__main__":
    server.run()