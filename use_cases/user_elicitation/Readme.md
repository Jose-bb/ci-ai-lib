# FastMCP Human-in-the-Loop (User Elicitation)

This use case provides a lightweight, resilient demonstration of the Human-in-the-Loop (HITL) pattern using the modern FastMCP framework. It showcases the `Elicitation` capability, allowing an AI tool or server to dynamically pause its asynchronous execution, request structured input from a human user via a client terminal, and safely resume the operation once the data is validated.

This specific implementation simulates a critical infrastructure action (`deploy_pytorch_model`) that requires explicit human authorization before a DevOps AI agent can deploy a machine learning model to production.

## Project Structure

- `src/`: 
  - `server.py`: The FastMCP server application. Exposes the deployment tool and defines the exact data structure it expects from the user during elicitation using a strict Pydantic schema.
  - `agent_client.py`: An autonomous client powered by Azure OpenAI. It dynamically extracts tools from the FastMCP server, reasons about the user's prompt, and decides to call the deployment tool on its own, triggering the HITL pause.
  - `deployment_agent.py`: *(Work in progress)* Orchestrator file designed to integrate the FastMCP tools into a LangGraph state graph.


## Features

- **Human-in-the-Loop (HITL) Architecture**: Prevents autonomous agents from executing destructive or highly sensitive actions without explicit human approval.
- **Autonomous Tool Calling**: Seamlessly translates MCP tools into OpenAI's native Function Calling format, allowing the LLM to trigger infrastructure actions.
- **Structured Data Elicitation**: Leverages `Pydantic` models on the server side to guarantee that the user's response is strongly typed and validated (e.g., forcing a boolean confirmation and an optional reason) before the tool resumes.
- **Asynchronous STDIO Transport**: The client and server communicate securely over standard input/output streams rather than HTTP, avoiding port conflicts.


## Running the Use Case

1. Ensure your virtual environment is active and dependencies are installed:
```bash
pip install -r use_cases/user_elicitation/requirements.txt
```
Copy the .env.example to a new .env file and fill in your Azure OpenAI credentials.

2. To see the AI agent reason about a prompt and autonomously trigger the deployment tool:
```bash
python use_cases/user_elicitation/src/client.py
```

3. Follow the terminal prompts to interact with the paused tool in real-time. Try answering with both yes and no to observe how the LLM summarizes the final outcome based on your authorization.