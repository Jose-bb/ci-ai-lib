import os
import shutil
import psutil
from pydantic import BaseModel, Field
from fastmcp import FastMCP, Context

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_USE_CASE_DIR = os.path.join(CURRENT_DIR, "..")

REGISTRY_DIR = os.path.join(BASE_USE_CASE_DIR, "data", "registry")
PROD_DIR = os.path.join(BASE_USE_CASE_DIR, "data", "production")

# Initialize the FastMCP server
server_name = os.getenv("MCP_SERVER_NAME", "ActionConfirmationServer")
server = FastMCP(server_name)

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
async def get_environment_health(environment: str) -> str:
    """Checks the REAL health and metrics of the machine running the server."""
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    mem_usage = memory_info.percent
    
    if cpu_usage > 85.0 or mem_usage > 90.0:
        return f"STATUS: YELLOW. Warning: High load detected on '{environment}'. CPU: {cpu_usage}%, RAM: {mem_usage}%. Proceed with caution."
        
    return f"STATUS: GREEN. Machine '{environment}' is healthy. CPU: {cpu_usage}%, RAM: {mem_usage}%. Ready for deployments."


@server.tool()
async def get_available_models() -> list[str]:
    """Reads the REAL files present in the local registry directory."""
    if not os.path.exists(REGISTRY_DIR):
        return []
    files = os.listdir(REGISTRY_DIR)
    return [f for f in files if f.endswith('.txt')]


@server.tool()
async def deploy_pytorch_model(model_name: str, target_environment: str, ctx: Context) -> str:
    """
    Physically copies a model file from the registry to the production folder.
    Requires explicit human confirmation via elicitation before copying.
    """
    if not model_name.endswith('.txt'):
        model_name = f"{model_name}.txt"

    elicitation_message = (
        f"DEPLOYMENT AUTHORIZATION: The agent is attempting to copy the file "
        f"'{model_name}' to the '{target_environment}' physical directory. "
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
    
    # Safely extract the Pydantic model
    if hasattr(user_input, 'content'):
        response_data = user_input.content
    elif hasattr(user_input, 'data'):
        response_data = user_input.data
    else:
        return f"Internal Error: Could not extract payload."
    
    # Now we safely use the extracted Pydantic model
    if not response_data.is_confirmed:
        return f"Operation blocked: User denied the deployment. Reason: {response_data.reason}"

    source_path = os.path.join(REGISTRY_DIR, model_name)
    
    # We map to the relevant production directory within 'data'
    if target_environment.lower() == "production":
        target_dir = PROD_DIR
    else:
        target_dir = os.path.join(BASE_USE_CASE_DIR, "data", target_environment.lower())
        os.makedirs(target_dir, exist_ok=True)
        
    dest_path = os.path.join(target_dir, model_name)
    
    if not os.path.exists(source_path):
        return f"Failure: The file '{model_name}' does not exist in the registry."
        
    try:
        shutil.copy2(source_path, dest_path)
        return f"Success: File '{model_name}' was physically copied to the '{target_environment}' folder. User authorization reason: {response_data.reason}"
    except Exception as e:
        return f"Critical Failure: Could not copy file. Error: {str(e)}"

if __name__ == "__main__":
    server.run()