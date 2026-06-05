import sys
import warnings
import argparse

# Eliminate flaml's harmless warning
warnings.filterwarnings("ignore", category=UserWarning, module="flaml")

from use_cases.a2a_protocols.src.swarm_setup import setup_swarm

def main():
    """
    Main entry point for the A2A Troubleshooting Swarm.
    Initializes the committee and submits the initial incident report.
    """
    # Handle dynamic input via CLI argument or interactive prompt
    parser = argparse.ArgumentParser(description="A2A Troubleshooting Swarm Orchestrator")
    parser.add_argument(
        "-i", "--incident", 
        type=str, 
        help="Provide the incident report directly via command line."
    )
    args = parser.parse_args()

    # Determine the incident report source
    if args.incident:
        incident_report = args.incident
    else:
        print("\n=== A2A Troubleshooting Swarm ===")
        incident_report = input("Please describe the technical incident to resolve:\n> ").strip()
        
        # Failsafe: Exit if the user simply presses Enter without typing anything
        if not incident_report:
            print("No incident provided. Exiting gracefully.")
            sys.exit(0)

    print("\nInitializing the Troubleshooting Swarm...")
    
    # Setup the swarm and get the proxy and manager
    try:
        proxy, manager = setup_swarm()
    except Exception as e:
        print(f"Error initializing the swarm: {e}")
        sys.exit(1)

    print("\n--- Starting the Committee Debate ---\n")
    
    # Initiate the chat
    proxy.initiate_chat(
        manager, 
        message=f"INCIDENT REPORT:\n{incident_report}", 
        summary_method="reflection_with_llm"
    )

    print("\n--- Committee Session Terminated ---")

if __name__ == "__main__":
    main()