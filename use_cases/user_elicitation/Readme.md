# FastMCP Human-in-the-Loop (User Elicitation)

This use case provides a lightweight, resilient demonstration of the Human-in-the-Loop (HITL) pattern using the modern FastMCP framework. It showcases the `Elicitation` capability, allowing an AI tool or server to dynamically pause its asynchronous execution, request structured input from a human user via a client terminal, and safely resume the operation once the data is validated.

This specific implementation simulates a critical infrastructure action (`restart_cluster`) that requires explicit human authorization before proceeding.

## Project Structure

- `src/`: 
  - `server.py`: The FastMCP server application. Exposes the tool and defines the exact data structure it expects from the user during elicitation using a strict Pydantic schema.
  - `client.py`: The FastMCP client application. Connects to the server via STDIO, executes the tool, and features a dedicated asynchronous handler to capture, format, and return the user's terminal input.

## Features

- **Human-in-the-Loop (HITL) Architecture**: Prevents autonomous agents from executing destructive or highly sensitive actions without explicit human approval.
- **Structured Data Elicitation**: Leverages `Pydantic` models on the server side to guarantee that the user's response is strongly typed and validated (e.g., forcing a boolean confirmation) before the tool resumes.

## Running the Use Case

1. Ensure your virtual environment is active and dependencies are installed:
    ```bash
    pip install -r use_cases/user_elicitation/requirements.txt
    ```
2. Run the client script directly from the repository root:
    ```bash
    python use_cases/user_elicitation/src/client.py
    ```
3. Follow the terminal prompts to interact with the paused tool in real-time. Try answering with both `yes` and `no` to observe how the server handles the blocking logic.