import psutil
from use_cases.a2a_protocols.src.tools.hitl_utils import request_human_approval

async def get_system_ram_cpu() -> str:
    """
    Checks the host machine's physical CPU usage and standard RAM (System Memory).
    Call this tool to rule out host-level bottlenecks or out-of-memory (RAM) crashes 
    before assuming it is a GPU (CUDA) issue.
    """
    # Centralized HITL call
    is_approved = await request_human_approval(
        prompt_message="Hardware_Specialist requests permission to read Host RAM and CPU metrics.",
        success_message="Reading system RAM and CPU..."
    )
    
    if not is_approved:
        return "ERROR: The human administrator denied permission to read system metrics."

    # Tool execution logic
    cpu_usage = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    
    total_ram_gb = round(ram.total / (1024**3), 2)
    used_ram_gb = round(ram.used / (1024**3), 2)
    free_ram_gb = round(ram.available / (1024**3), 2)
    
    return (
        f"\n[REAL SYSTEM HEALTH METRICS]\n"
        f"CPU Usage: {cpu_usage}%\n"
        f"Total Host RAM: {total_ram_gb} GB\n"
        f"Used Host RAM: {used_ram_gb} GB ({ram.percent}%)\n"
        f"Available Host RAM: {free_ram_gb} GB\n"
    )