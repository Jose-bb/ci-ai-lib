import sys
import warnings

# Eliminate flaml's harmless warning
warnings.filterwarnings("ignore", category=UserWarning, module="flaml")

from use_cases.a2a_protocols.src.swarm_setup import setup_swarm

def main():
    """
    Main entry point for the A2A Troubleshooting Swarm.
    Initializes the committee and submits the initial incident report.
    """
    print("Initializing the Troubleshooting Swarm...")
    
    # Setup the swarm and get the proxy and manager
    try:
        proxy, manager = setup_swarm()
    except Exception as e:
        print(f"Error initializing the swarm: {e}")
        sys.exit(1)

    # Define the complex incident to resolve
    incident_report = (
        "INCIDENT REPORT:\n"
        "We are trying to deploy a local instance of a quantized LLM (Llama-3-8B-Instruct) "
        "using vLLM inside a Docker container. "
        "However, the deployment crashes exactly 45 seconds after starting, throwing an "
        "'OOM (Out Of Memory) - CUDA error: out of memory' exception. "
        "The host machine has an RTX 4090 (24GB VRAM), and no other heavy processes are running. "
        "Team, please analyze the situation, identify the root cause, and propose a concrete "
        "configuration or code fix to successfully deploy the model."
    )

    print("\n--- Starting the Committee Debate ---\n")
    
    # Initiate the chat
    proxy.initiate_chat(
        manager,
        message=incident_report,
        summary_method="reflection_with_llm", 
    )

    print("\n--- Committee Session Terminated ---")

if __name__ == "__main__":
    main()