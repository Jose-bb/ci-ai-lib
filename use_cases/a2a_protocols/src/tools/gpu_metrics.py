import subprocess
from use_cases.a2a_protocols.src.tools.hitl_utils import request_human_approval

async def get_vram_status() -> str:
    """
    Checks the current GPU VRAM allocation and identifies processes consuming memory.
    Call this tool when you need to diagnose CUDA Out-Of-Memory (OOM) errors 
    or check physical hardware constraints.
    """
    # Centralized HITL call
    is_approved = await request_human_approval(
        prompt_message="The Hardware_Specialist is requesting permission to execute: 'get_vram_status'",
        success_message="Executing nvidia-smi on the host machine..."
    )
    
    if not is_approved:
        return "ERROR: The human administrator denied permission to execute this tool."

    # Tool execution logic
    try:
        # Execute the command
        result = subprocess.check_output(
            ["nvidia-smi"], 
            encoding="utf-8", 
            stderr=subprocess.STDOUT
        )
        return f"\n[REAL SYSTEM RESPONSE - nvidia-smi]\n{result}"
        
    except FileNotFoundError:
        return "ERROR: 'nvidia-smi' command not found."
    except subprocess.CalledProcessError as e:
        return f"ERROR: 'nvidia-smi' execution failed with exit code {e.returncode}. Output:\n{e.output}"