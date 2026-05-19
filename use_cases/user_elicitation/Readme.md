# FastMCP Human-in-the-Loop (User Elicitation)

This use case provides a lightweight, resilient demonstration of the Human-in-the-Loop (HITL) pattern using the modern FastMCP framework. It showcases the `Elicitation` capability, allowing an AI tool or server to dynamically pause its asynchronous execution, request structured input from a human user via a client terminal, and safely resume the operation once the data is validated.

This specific implementation simulates a critical infrastructure action (`deploy_pytorch_model`) that requires explicit human authorization before a DevOps AI agent can deploy a machine learning model to production.

## Project Structure

- `src/`: 
  - `server.py`: The FastMCP server application. Exposes the deployment tool, performs real system health checks (`psutil`), handles physical file operations (`shutil`), and defines the Pydantic schema for elicitation.
  - `deployment_agent.py`: An interactive, terminal-based DevOps AI chatbot powered by LangGraph and Azure OpenAI. It maintains conversational memory, extracts tools from the FastMCP server, and triggers the HITL pause when a deployment is requested.
- `data/`: Contains the `registry/` (source dummy models, e.g., `.txt` files) and `production/` directories to simulate physical file manipulation.
- `test/`: Pytest suite featuring unit tests with `unittest.mock` to validate the elicitation logic, agent boundaries, and server operations safely.


## Features

- **Human-in-the-Loop (HITL) Architecture**: Prevents autonomous agents from executing destructive or highly sensitive actions without explicit human approval.
- **Autonomous Tool Calling**: Seamlessly translates MCP tools into OpenAI's native Function Calling format, allowing the LLM to trigger infrastructure actions.
- **Structured Data Elicitation**: Leverages `Pydantic` models on the server side to guarantee that the user's response is strongly typed and validated (e.g., forcing a boolean confirmation and an optional reason) before the tool resumes.
- **Asynchronous STDIO Transport**: The client and server communicate securely over standard input/output streams rather than HTTP, avoiding port conflicts.
- **Interactive Console Chat**: Utilizes LangGraph's `StateGraph` and message arrays to provide a continuous, context-aware terminal interface.
- **Physical System Integration**: Interacts with the real host OS to check CPU/RAM usage and physically copy files between directories.
- **Robust Testing Suite**: Includes automated unit tests (using `pytest` and `unittest.mock`) to validate the human-in-the-loop logic without triggering real deployments or consuming LLM API tokens.


## Running the Use Case

1. Ensure your virtual environment is active and dependencies are installed:
```bash
pip install -r use_cases/user_elicitation/requirements.txt
```
Copy the .env.example to a new .env file and fill in your Azure OpenAI credentials.

2. To see the AI agent reason about a prompt and autonomously trigger the deployment tool:
```bash
python use_cases/user_elicitation/src/deployment_agent.py
```

3. Interact with the agent naturally in the terminal. Ask it to list available models, check system health, and finally command it to deploy a model. FastMCP will pause the execution and request your explicit authorization before copying any files. Type quit or exit to close the agent gracefully.


## Running Tests

The test suite heavily utilizes `unittest.mock` to isolate the core logic. This ensures that the tests execute in milliseconds, do not consume Azure OpenAI tokens, and do not mutate your real local file system.

To run the automated test suite and verify the integrity of the agent's logic, execute:
  ```bash
  pytest use_cases/user_elicitation/test/ -v
  ```