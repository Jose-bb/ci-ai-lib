# Automated Tests Generator: LangGraph QA Agent (V1)

This use case provides a FastAPI endpoint that acts as an autonomous Quality Assurance engineer. Powered by LangGraph, Azure OpenAI, and Pydantic, it ingests raw Python source code, analyzes its structure, and orchestrates a multi-step pipeline. The agent generates a comprehensive test plan (covering happy paths, edge cases, and exception handling) and outputs an executable `pytest` suite that strictly utilizes `unittest.mock` to isolate dependencies.

*Note: This is the V1 (MVP) architecture. It is designed to process raw code strings. Future versions will support full repository ingestion via `.zip` uploads and Git URLs.*

## Project Structure

- `src/`: 
  - `main.py`: FastAPI application entry point. Initializes the LangGraph on startup to minimize latency.
  - `generator_graph.py`: LangGraph orchestrator containing the state management and the three core nodes (`parser_node`, `qa_planner_node`, `test_coder_node`).
  - `prompts.py`: Static system prompts and rigid instructions for both the QA Planner and Test Coder agents.
- `tests/`:
  - `test_generator.py`: Contains unit tests for the LangGraph agent and the FastAPI endpoint.
- `utilities/`:
  - `parser.py`: Utility module that safely extracts classes and functions from the ingested Python code.
- `Dockerfile`: Containerization setup for this microservice.


## Features

- **Multi-Agent Orchestration (LangGraph)**: Sequential processing pipeline where the output of the planning phase directly conditions the behavior of the coding phase.
- **QA Planning First**: Before writing any code, the agent generates a strategic Markdown document evaluating edge cases, invalid inputs, and happy paths to ensure 100% logic coverage.
- **Mock-Driven Generation**: Strict system prompting ensures the generated `pytest` code relies heavily on `unittest.mock.patch` and `@pytest.fixture`, guaranteeing that the output tests are isolated and do not make real network calls or DB transactions.
- **Pydantic Validation**: Ensures the incoming payload strictly matches the required schema (`GenerationRequest`), rejecting malformed requests immediately with HTTP 422.
- **FastAPI Integration**: Clean and fast API endpoints with Swagger UI documentation.


## API Endpoints

- `POST /generate-tests`: Accepts raw Python code and a module name. Returns a JSON payload containing the parsed test plan and the final `pytest` code block.
- `GET /health`: Health check.

### Example Request

```json
{
  "source_code": "class Calculator:\n    def divide(self, a, b):\n        return a / b\n\ndef greet(name):\n    if not name:\n        return 'Hello, World!'\n    return f'Hello, {name}!'",
  "module_name": "basic_math"
}
```


## Running the Use Case

1. Configure your `.env` file in the root directory.
2. Build and spin up the container using Docker Compose:
   ```bash
   docker compose up --build -d tests-generator
   ```
3. The API will be available at http://localhost:8003/docs


## Running Tests

### Automated Testing (Pytest)

The internal test suite for this module is completely isolated. It uses a hybrid strategy of `unittest.mock.patch` and Pytest fixtures to intercept the LangGraph nodes. This ensures that testing the architecture does not consume real Azure OpenAI tokens, executes in milliseconds, and runs perfectly offline.

To run the automated test suite and verify the integrity of the graph routing, error handling, and API responses, run:
  ```bash
  docker compose run --rm tests-generator pytest use_cases/tests_generator/tests/
  ```
