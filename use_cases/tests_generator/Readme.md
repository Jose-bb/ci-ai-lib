# Automated Tests Generator: LangGraph QA Agent (V3)

This use case provides a FastAPI endpoint that acts as an autonomous Quality Assurance engineer. Powered by LangGraph, Azure OpenAI, and native Python libraries, it ingests full project repositories via `.zip` uploads or **direct Git URLs**, analyzes the global structure, and orchestrates a multi-step pipeline. 

The architecture is fully asynchronous. It utilizes background tasks and a global state callback system to provide real-time progress tracking without blocking the main event loop. The agent generates a comprehensive test plan and outputs a global, executable `pytest` suite that strictly utilizes `unittest.mock` to isolate dependencies. The final artifacts are packaged and delivered as a downloadable `.zip` file.

## Project Structure

- `src/`: 
  - `main.py`: FastAPI application entry point. Handles async task queuing, progress state storage, and exposes endpoints for ZIP/Git ingestion and status polling.
  - `generator_graph.py`: LangGraph orchestrator containing the state management, progress callbacks, and the core nodes (`parser_node`, `qa_planner_node`, `test_coder_node`).
  - `prompts.py`: Static system prompts and rigid instructions for both the QA Planner and Test Coder agents.
- `tests/`:
  - `test_generator.py`: Contains unit tests for the LangGraph agent and the FastAPI endpoint.
- `utilities/`:
  - `parser.py`: Utility module that safely extracts a global hierarchical map of classes and functions from all ingested Python files.
  - `zip_extractor.py`: Handles in-memory extraction, sanitization (ignoring macOS/hidden files), and filtering of `.zip` uploads.
  - `git_extractor.py`: Handles cloning, temporary storage, and extraction of Python files directly from public GitHub repositories.
- `Dockerfile`: Containerization setup for this microservice.


## Features

- **Multi-Agent Orchestration (LangGraph)**: Sequential processing pipeline where the output of the planning phase directly conditions the behavior of the coding phase.
- **Global Project Context**: The parser reads and maps the entire architecture of the uploaded `.zip`, allowing the LLM to understand how modules interact before writing tests.
- **Mock-Driven Generation**: Strict system prompting ensures the generated `pytest` code relies heavily on `unittest.mock.patch` and `@pytest.fixture`, guaranteeing that the output tests are isolated.
- **In-Memory Zip Processing**: Uploads and downloads are processed entirely in RAM using `io.BytesIO`, avoiding disk I/O bottlenecks and ensuring security.
- **Fail-Fast Validations**: The API strictly enforces `.zip` file extensions and captures syntax errors during the parsing phase to halt graph execution, saving LLM tokens.
- **Asynchronous Architecture**: Utilizes FastAPI `BackgroundTasks` to offload heavy LLM computations and repository cloning, instantly returning a `202 Accepted` status with a unique Task ID.
- **Real-Time Progress Tracking**: Injects a closure-based callback directly into the LangGraph state, allowing the AI nodes to update their percentage and status messages dynamically for the frontend to poll.
- **Git Repository Ingestion**: Bypasses manual ZIP creation by directly pulling code from public Git URLs via the `GitExtractor`.


## API Endpoints

- `POST /generate-tests-from-zip`: Accepts a `.zip` file containing Python source code. Queues the task and returns a `202 Accepted` with a `task_id`.
- `POST /generate-tests-from-git`: Accepts a JSON payload `{"repo_url": "..."}`. Queues the task and returns a `202 Accepted` with a `task_id`.
- `GET /status/{task_id}`: Polls the current status of the task. 
  - Returns a JSON with `progress` (0-100) and `message` if still processing.
  - Returns the downloadable `.zip` file containing the Markdown test plan and `pytest` suite if completed.
  - Returns a `400 Bad Request` if the graph encountered a syntax error or cloning failure.
- `GET /health`: Health check.

### Example Async Workflow

You can test the asynchronous workflow directly via the Swagger UI (http://localhost:8003/docs):

1. Submit a repository URL to `/generate-tests-from-git`.
2. Copy the `task_id` from the response body.
3. Call `/status/{task_id}` repeatedly to watch the `progress` percentage and `message` update in real-time.
4. Once progress reaches 100%, the endpoint will automatically serve the final `.zip` file.


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
