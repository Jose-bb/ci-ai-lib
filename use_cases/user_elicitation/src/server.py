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
async def restart_cluster(cluster_name: str, ctx: Context) -> str:
    """
    Simulates restarting a critical infrastructure cluster.
    Requires explicit human confirmation via elicitation before proceeding.
    
    Args:
        cluster_name: The name of the cluster to restart.
        ctx: The FastMCP Context object used to trigger elicitation.
    """
    elicitation_message = (
        f"CRITICAL ACTION: The system is attempting to restart the cluster '{cluster_name}'. "
        f"Do you explicitly approve this action?"
    )
    
    # Trigger elicitation
    user_input = await ctx.elicit(
        elicitation_message,
        response_type=ConfirmationResponse
    )
    
    # Handle the user's response
    if not user_input:
        return f"Operation aborted: User declined or cancelled the elicitation request for '{cluster_name}'."

    if hasattr(user_input, 'content'):
        response_data = user_input.content
    elif hasattr(user_input, 'data'):
        response_data = user_input.data
    else:
        print(f"\n[SERVER DEBUG] Unknown wrapper structure. Attributes: {dir(user_input)}\n")
        return f"Internal Error: Could not extract payload from {type(user_input).__name__}."
        
    # Now we safely use the extracted Pydantic model
    if not response_data.is_confirmed:
        return f"Operation blocked: User explicitly denied the restart. Reason: {response_data.reason}"
        
    return f"Success: Cluster '{cluster_name}' is restarting. User authorization reason: {response_data.reason}"

if __name__ == "__main__":
    server.run()