# Agent-to-Agent (A2A) Troubleshooting Swarm (V2)

This use case demonstrates an advanced Multi-Agent system built with Microsoft AutoGen. It provides a real-time, autonomous Agent-to-Agent collaboration environment that goes beyond pure conversation by actively executing physical system diagnostic tools to resolve complex technical incidents.

In this architecture, a Software Engineer, a Hardware Specialist, and a Chief Architect debate a dynamic, user-provided incident (e.g., CUDA Out-Of-Memory errors or Docker crashes). The swarm is supervised by a Human User Proxy and executes real-world hardware and container metrics, showcasing dynamic role-based routing, proactive tool execution, and autonomous consensus without requiring a web interface.

## Project Structure

- `src/`: 
  - `main.py`: The main entry point and CLI orchestrator. It uses `argparse` to dynamically ingest the incident report from the terminal, initializes the swarm, and triggers the AutoGen chat mechanism.
  - `agents.py`: Defines the system prompts, boundaries, and personalities of the distinct AutoGen agents (`user_proxy`, `software_agent`, `hardware_agent`, `architect_agent`). Includes tool-awareness directives (proactive delegation) and a specialized client-facing role for the Architect.
  - `swarm_setup.py`: Configures the Azure OpenAI LLM connections, handles the secure injection of authentication headers, and iterates through a DRY tool registry to map Python functions to specific agents.
  - `tools/`: Contains the functional capabilities that agents can execute autonomously:
    - `gpu_metrics.py`: Executes `nvidia-smi` to extract real-time VRAM saturation.
    - `system_health.py`: Uses `psutil` to extract physical host RAM and CPU metrics.
    - `docker_logs.py`: Interfaces with the Docker API to extract recent container crash logs.
- `test/`:
  - `test_a2a_protocols.py`: Contains the unit test suite for the swarm architecture, ensuring routing, dynamic CLI inputs, tool registration, and initialization work perfectly using `unittest.mock`.
- `workspace/`: Isolated directory designated for AutoGen's internal file I/O operations and autonomous code execution environments, resolved via dynamic absolute paths.
*- `Dockerfile`: Containerization setup for this microservice in upcoming versions.*


## Features

- **Proactive Tool Execution (Function Calling)**: Agents dynamically assess the incident and invoke registered Python tools to interact with the host system (e.g., fetching Docker logs or reading real-time GPU memory metrics) instead of making blind assumptions.
- **Human-in-the-Loop (HITL) Firewall**: All system-level tool executions requested by the AI trigger a terminal security alert, pausing the swarm until the human administrator explicitly approves or denies the action.
- **Autonomous Multi-Agent Debate**: Agents interact directly with each other without constant human intervention, guided logically by a `GroupChatManager` that selects the next best speaker based on the conversation history and required domain.
- **Role-Based Expertise & Delegation**: Strict system prompts restrict agents to their specific domain. Agents are explicitly instructed to cross-delegate tasks if a peer possesses a diagnostic tool better suited for the required metric.
- **Client-Facing Architect**: A designated Chief Architect agent evaluates peer proposals, consolidates the raw technical tool data, and acts as the sole client-facing entity to present the human user with clear, jargon-free options.
- **Mock-Driven Architecture Validation**: A comprehensive Pytest suite intercepts LLM API calls, CLI arguments, and system limits to validate the AutoGen routing logic, tool registry, and orchestrator stability entirely offline.


## Running the Use Case

V2 is a dynamic CLI-based application. To experience the real-time agent debate and tool execution, use the `--incident` flag from your virtual environment:

1. Configure your `.env` file in the root directory.
2. Run the orchestrator from the root of the repository, providing your technical issue:
  ```bash
  python -m use_cases.a2a_protocols.src.main --incident "We are trying to deploy Llama-3-8B in a Docker container named 'vllm-server'. It crashes after 45s with an 'OOM' error."
  ```
  Or simply execute the file:
  ```bash
  python -m use_cases.a2a_protocols.src.main
  ```
3. Approve Tool Calls: When an agent attempts to run a diagnostic tool (like reading system RAM), the console will display a SECURITY ALERT. Type y or n to authorize it.
4. Watch the agents debate. When the Chief Architect emits the TERMINATE signal, the console will pause, allowing you to provide feedback or type exit to close the session.


## Running Tests

### Automated Testing (Pytest)

The internal test suite for this module isolates the AutoGen architecture from the actual Azure OpenAI network calls and physical system executions. It uses `unittest.mock.patch` to intercept CLI inputs, validate the tool registry loop, and ensure the failsafes trigger correctly.

To run the automated test suite, execute the following command from the root of the repository:
  ```bash
  pytest .\use_cases\a2a_protocols\test\test_a2a_protocols.py
  ```