# Automated Tests Generator: LangGraph QA Agent (V2)

This use case provides a FastAPI endpoint that acts as an autonomous Quality Assurance engineer. Powered by LangGraph, Azure OpenAI, and native Python libraries, it ingests full project repositories via `.zip` uploads, analyzes the global structure, and orchestrates a multi-step pipeline. The agent generates a comprehensive test plan and outputs a global, executable `pytest` suite that strictly utilizes `unittest.mock` to isolate dependencies. The final artifacts are packaged and delivered as a downloadable `.zip` file.

*Note: This is the V2 architecture. It is designed to process full repository ingestion via `.zip` uploads. Future versions will support full repository ingestion via Git URLs.*

## Project Structure

- `src/`: 
  - `main.py`: FastAPI application entry point. Handles `multipart/form-data` uploads, streaming responses, and initializes the LangGraph.
  - `generator_graph.py`: LangGraph orchestrator containing the state management and the three core nodes (`parser_node`, `qa_planner_node`, `test_coder_node`).
  - `prompts.py`: Static system prompts and rigid instructions for both the QA Planner and Test Coder agents.
- `tests/`:
  - `test_generator.py`: Contains unit tests for the LangGraph agent and the FastAPI endpoint.
- `utilities/`:
  - `parser.py`: Utility module that safely extracts a global hierarchical map of classes and functions from all ingested Python files.
  - `zip_extractor.py`: Handles in-memory extraction, sanitization (ignoring macOS/hidden files), and filtering of `.zip` uploads.
- `Dockerfile`: Containerization setup for this microservice.


## Features

- **Multi-Agent Orchestration (LangGraph)**: Sequential processing pipeline where the output of the planning phase directly conditions the behavior of the coding phase.
- **Global Project Context**: The parser reads and maps the entire architecture of the uploaded `.zip`, allowing the LLM to understand how modules interact before writing tests.
- **Mock-Driven Generation**: Strict system prompting ensures the generated `pytest` code relies heavily on `unittest.mock.patch` and `@pytest.fixture`, guaranteeing that the output tests are isolated.
- **In-Memory Zip Processing**: Uploads and downloads are processed entirely in RAM using `io.BytesIO`, avoiding disk I/O bottlenecks and ensuring security.
- **Fail-Fast Validations**: The API strictly enforces `.zip` file extensions and captures syntax errors during the parsing phase to halt graph execution, saving LLM tokens.


## API Endpoints

- `POST /generate-tests-from-zip`: Accepts a `.zip` file containing Python source code. Returns a downloadable `.zip` file containing the generated Markdown test plan and the `pytest` suite.
- `GET /health`: Health check.

### Example Request

Since the endpoint now expects a `multipart/form-data` payload, you can test it directly via the Swagger UI (http://localhost:8003/docs) by uploading a file.


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
