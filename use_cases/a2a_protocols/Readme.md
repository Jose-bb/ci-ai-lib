# Agent-to-Agent (A2A) Troubleshooting Swarm (V3)

This use case demonstrates an advanced Multi-Agent system built with Microsoft AutoGen and FastAPI. It provides a real-time, autonomous Agent-to-Agent collaboration environment bridged over WebSockets that goes beyond pure conversation by actively executing physical system diagnostic tools to resolve complex technical incidents.

In this architecture, a Software Engineer, a Hardware Specialist, and a Chief Architect debate a dynamic, user-provided incident (e.g., CUDA Out-Of-Memory errors or Docker crashes). The swarm is supervised by a Human User Proxy and executes real-world hardware and container metrics, showcasing dynamic role-based routing, proactive tool execution, thread-safe Human-in-the-Loop (HITL) concurrency, and real-time observability telemetry through a dedicated Web UI.

## Project Structure

- `src/`: 
  - `main.py`: The main entry point. Rebuilt as a FastAPI application handling asynchronous WebSocket connections to dynamically instantiate the swarm and stream the incident debate.
  - `agents.py`: Defines the system prompts, boundaries, and personalities of the distinct AutoGen agents (`user_proxy`, `software_agent`, `hardware_agent`, `architect_agent`). Includes tool-awareness directives (proactive delegation) and a specialized client-facing role for the Architect.
  - `swarm_setup.py`: Configures the Azure OpenAI LLM connections, handles the secure injection of authentication headers, and iterates through a DRY tool registry to map Python functions to specific agents.
  - `tools/`: Contains the functional capabilities that agents can execute autonomously:
    - `tools_utils/`: Sub-package housing isolated utilities for tool execution:
      - `hitl_utils.py`: Manages the terminal/WebSocket Human-in-the-Loop approval requests.
      - `tools_telemetry.py`: Contains the `@measure_latency` async decorator to track physical tool execution times.
    - `gpu_metrics.py`: Executes `nvidia-smi` to extract real-time VRAM saturation.
    - `system_health.py`: Uses `psutil` to extract physical host RAM and CPU metrics.
    - `docker_logs.py`: Interfaces with the Docker API to extract recent container crash logs.
- `test/`:
  - `test_a2a_protocols.py`: Upgraded async test suite utilizing `pytest-asyncio` and `AsyncMock` to validate WebSocket proxies, concurrency locks, and telemetry middleware hooks.
- `workspace/`: Isolated directory designated for AutoGen's internal file I/O operations and autonomous code execution environments, resolved via dynamic absolute paths.
- `utilities/`: 
  - `frontend/`: Contains the vanilla client (`test_ws.html`, `styles.css`) acting as the interactive user simulator and real-time telemetry dashboard.
  - `cost_tracker.py`: AutoGen middleware utility to calculate precise USD token consumption for lightweight models (e.g., gpt-4o-mini).
- `Dockerfile`: Fully containerized setup integrating the FastAPI server with internal system tools and isolated Python environments.


## Features

- **Proactive Tool Execution (Function Calling)**: Agents dynamically assess the incident and invoke registered Python tools to interact with the host system (e.g., fetching Docker logs or reading real-time GPU memory metrics) instead of making blind assumptions.
- **Human-in-the-Loop (HITL) Firewall**: All system-level tool executions requested by the AI trigger a terminal security alert, pausing the swarm until the human administrator explicitly approves or denies the action.
- **Autonomous Multi-Agent Debate**: Agents interact directly with each other without constant human intervention, guided logically by a `GroupChatManager` that selects the next best speaker based on the conversation history and required domain.
- **Role-Based Expertise & Delegation**: Strict system prompts restrict agents to their specific domain. Agents are explicitly instructed to cross-delegate tasks if a peer possesses a diagnostic tool better suited for the required metric.
- **Client-Facing Architect**: A designated Chief Architect agent evaluates peer proposals, consolidates the raw technical tool data, and acts as the sole client-facing entity to present the human user with clear, jargon-free options.
- **Mock-Driven Architecture Validation**: A comprehensive Pytest suite intercepts LLM API calls, CLI arguments, and system limits to validate the AutoGen routing logic, tool registry, and orchestrator stability entirely offline.
- **End-to-End Async WebSockets**: The orchestrator runs entirely asynchronously, streaming the agent debate in real-time to a custom HTML/CSS frontend without blocking operations.
- **Thread-Safe Concurrency (Async Locks)**: Employs `asyncio.Lock()` to prevent the backend from crashing or spamming the UI when multiple agents attempt to execute restricted physical tools simultaneously.
- **Event-Driven Telemetry & Cost Tracking**: Custom Python decorators and AutoGen middleware hooks (`process_message_before_send`) intercept LLM token usage and tool latency, broadcasting operational metrics to a dedicated split-screen UI dashboard.


## Running the Use Case

V3 is a fully containerized asynchronous application. To experience the real-time agent debate and telemetry:

1. Configure your `.env` file in the root directory.
2. Build and start the Docker container to isolate the tool execution environment:
  ```bash
  docker compose up --build -d a2a-protocols
  ```
3. Open the frontend simulator by double-clicking utilities/frontend/test_ws.html in your web browser.
4. Type your technical issue (e.g., "Docker memory crash") in the input box and interact directly with the swarm via the Web UI.

## Running Tests

### Automated Testing (Pytest Asyncio)

The V3 test suite isolates the AutoGen architecture from the Azure OpenAI network and physical system executions. It heavily utilizes `AsyncMock` to intercept WebSocket payloads, validate the custom token cost mathematics, and ensure the middleware hooks do not modify the original LLM messages.

To run the automated test suite, execute the following command from the root of the repository:
  ```bash
  pytest .\use_cases\a2a_protocols\test\test_a2a_protocols.py
  ```