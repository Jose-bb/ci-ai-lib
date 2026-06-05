import subprocess

def get_docker_logs(container_name: str) -> str:
    """
    Fetches the last 30 lines of logs from a specified Docker container.
    Call this tool when you need to diagnose application crashes, 
    initialization errors, or container failures.
    """
    # HITL firewall
    print("\n" + "="*60)
    print(f"SECURITY ALERT: Software_Engineer requests to read logs from Docker container: '{container_name}'")
    print("="*60)
    
    while True:
        user_input = input("Do you approve this execution? (y/n): ").strip().lower()
        if user_input in ['y', 'yes']:
            print(f"[+] Access GRANTED. Fetching logs for {container_name}...\n")
            break
        elif user_input in ['n', 'no']:
            print("[-] Access DENIED by User.\n")
            return "ERROR: The human administrator denied permission to read Docker logs."
        else:
            print("Invalid input. Please type 'y' for Yes, or 'n' for No.")

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