# Agent-to-Agent (A2A) Troubleshooting Swarm (V1)

This use case demonstrates a purely conversational Multi-Agent system built with Microsoft AutoGen. It provides a real-time, autonomous Agent-to-Agent collaboration environment designed to resolve complex technical incidents. 

In this architecture, a Software Engineer, a Hardware Specialist, and a Chief Architect debate a hardcoded CUDA Out-Of-Memory (OOM) error. The swarm is supervised by a Human User Proxy, running directly in the terminal to showcase dynamic role-based routing, logical reasoning, and autonomous consensus without requiring a web interface.

## Project Structure

- `src/`: 
  - `main.py`: The main entry point and CLI orchestrator. It initializes the swarm, injects the initial incident report, and triggers the AutoGen chat mechanism.
  - `agents.py`: Defines the system prompts, boundaries, and personalities of the distinct AutoGen agents (`user_proxy`, `software_agent`, `hardware_agent`, `architect_agent`). Includes the custom lambda function for termination logic.
  - `swarm_setup.py`: Configures the Azure OpenAI LLM connections, handles the secure injection of authentication headers, and instantiates the core `GroupChat` and `GroupChatManager`.
  *- `tools/`: Directory reserved for the implementation of custom Python functions (Tools) in that the agents will be authorized to execute in upcoming versions (e.g., dynamic hardware profiling or system reads).*
- `test/`:
  - `test_a2a_protocols.py`: Contains the unit test suite for the swarm architecture, ensuring routing and initialization work perfectly using `unittest.mock`.
- `workspace/`: Isolated directory designated for AutoGen's internal file I/O operations, agent logs, and future code execution environments.
*- `Dockerfile`: Containerization setup for this microservice in upcoming versions.*


## Features

- **Autonomous Multi-Agent Debate**: Agents interact directly with each other without constant human intervention, guided logically by a `GroupChatManager` that selects the next best speaker based on the conversation history.
- **Role-Based Expertise**: Strict system prompts restrict agents to their specific domain (Hardware configurations vs. Software/Code fixes), forcing cross-disciplinary collaborative problem-solving.
- **Architectural Synthesis**: A designated Chief Architect agent evaluates peer proposals, consolidates the technical data, and makes the final actionable decision.
- **Human-in-the-Loop (User Elicitation)**: The User Proxy agent serves as the human administrator. It can interject to provide constraints or simply validate the final decisions, utilizing a secure `TERMINATE` keyword interception to halt the execution loop gracefully.
- **Mock-Driven Architecture Validation**: A comprehensive Pytest suite intercepts LLM API calls, environment variables, and system exits to validate the AutoGen routing logic and orchestrator stability entirely offline, without consuming Azure tokens.


## Running the Use Case

Currently, V1 is a conversational CLI-based application. To experience the real-time agent debate, execute the module directly from your virtual environment:

1. Configure your `.env` file in the root directory.
2. Run the orchestrator from the root of the repository:
  ```bash
  python -m use_cases.a2a_protocols.src.main
  ```
3. Watch the agents debate. When the Chief Architect emits the `TERMINATE` signal, the console will pause, allowing you to provide feedback or type `exit` to close the session.


## Running Tests

### Automated Testing (Pytest)

The internal test suite for this module isolates the AutoGen architecture from the actual Azure OpenAI network calls. It uses `unittest.mock.patch` to intercept the initialization sequence, validate the routing constraints, and ensure the `sys.exit` failsafes trigger correctly on bad configurations.

To run the automated test suite, execute the following command from the root of the repository:
  ```bash
  pytest .\use_cases\a2a_protocols\test\test_a2a_protocols.py
  ```