import psutil

def get_system_ram_cpu() -> str:
    """
    Checks the host machine's physical CPU usage and standard RAM (System Memory).
    Call this tool to rule out host-level bottlenecks or out-of-memory (RAM) crashes 
    before assuming it is a GPU (CUDA) issue.
    """
    # HITL firewall
    print("\n" + "="*60)
    print("SECURITY ALERT: Hardware_Specialist requests permission to read Host RAM and CPU metrics.")
    print("="*60)
    
    while True:
        user_input = input("Do you approve this execution? (y/n): ").strip().lower()
        if user_input in ['y', 'yes']:
            print("[+] Access GRANTED. Reading system RAM and CPU...\n")
            break
        elif user_input in ['n', 'no']:
            print("[-] Access DENIED by User.\n")
            return "ERROR: The human administrator denied permission to read system metrics."
        else:
            print("Invalid input. Please type 'y' for Yes, or 'n' for No.")

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