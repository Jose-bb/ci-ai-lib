import subprocess
from use_cases.a2a_protocols.src.tools.hitl_utils import request_human_approval

async def get_docker_logs(container_name: str) -> str:
    """
    Fetches the last 30 lines of logs from a specified Docker container.
    Call this tool when you need to diagnose application crashes, 
    initialization errors, or container failures.
    """
    # Centralized HITL call
    is_approved = await request_human_approval(
        prompt_message=f"Software_Engineer requests to read logs from Docker container: '{container_name}'",
        success_message=f"Fetching logs for {container_name}..."
    )
    
    if not is_approved:
        return "ERROR: The human administrator denied permission to read Docker logs."

    # Tool execution logic
    try:
        # Execute: docker logs --tail 30 <container_name>
        result = subprocess.check_output(
            ["docker", "logs", "--tail", "30", container_name], 
            encoding="utf-8", 
            stderr=subprocess.STDOUT
        )
        return f"\n[REAL DOCKER LOGS - {container_name}]\n{result}"
        
    except FileNotFoundError:
        return "ERROR: 'docker' command not found. Ensure Docker is installed and running."
    except subprocess.CalledProcessError as e:
        return f"ERROR: Failed to fetch logs for '{container_name}'. It may not exist. Output:\n{e.output}"