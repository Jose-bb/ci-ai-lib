import subprocess

def get_vram_status() -> str:
    """
    Checks the current GPU VRAM allocation and identifies processes consuming memory.
    Call this tool when you need to diagnose CUDA Out-Of-Memory (OOM) errors 
    or check physical hardware constraints.
    """
    # HITL firewall
    print("\n" + "="*60)
    print("SECURITY ALERT: The Hardware_Specialist is requesting permission to execute: 'get_vram_status'")
    print("="*60)
    
    while True:
        user_input = input("Do you approve this execution? (y/n): ").strip().lower()
        if user_input in ['y', 'yes']:
            print("[+] Access GRANTED. Executing nvidia-smi on the host machine...\n")
            break
        elif user_input in ['n', 'no']:
            print("[-] Access DENIED by User.\n")
            return "ERROR: The human administrator denied permission to execute this tool. You must diagnose the issue without this hardware data."
        else:
            print("Invalid input. Please type 'y' for Yes, or 'n' for No.")

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
        return (
            "ERROR: 'nvidia-smi' command not found. "
            "Ensure NVIDIA drivers are installed and accessible in the system PATH."
        )
    except subprocess.CalledProcessError as e:
        return f"ERROR: 'nvidia-smi' execution failed with exit code {e.returncode}. Output:\n{e.output}"