# Multi-Agent VecDB Router with PII Privacy, Redis Memory, SSE Streaming & Full Observability (V3)

This use case provides a FastAPI endpoint that acts as an intelligent, multi-domain Retrieval-Augmented Generation (RAG) system. Powered by LangGraph, ChromaDB, Azure OpenAI, Microsoft Presidio, Redis, and Arize Phoenix, it evaluates natural language questions, routes them to the appropriate knowledge base based on a YAML configuration, performs semantic search to retrieve relevant context, and generates highly accurate, hallucination-free answers while maintaining persistent conversational memory for multi-turn context.


## Project Structure

- `config/`:
  - `prompts.yaml`: The core configuration driving the LLM rules, and collection routing logic.
- `src/`: 
  - `main.py`: FastAPI application entry point.
  - `supervisor.py`: LangGraph orchestrator that routes user intent to the correct knowledge domain and manages conversational state with Redis.
  - `rag_agent.py`: Worker agent that injects retrieved context into prompts to generate grounded, natural language answers.
  - `vector_engine.py`: Engine responsible for embedding text and interacting with ChromaDB for similarity search.
- `data/`: Contains the raw knowledge files (TXT, CSV, PDF) organized by domain. **The subfolder names inside this directory must exactly match the `collection_name` variables defined in your `prompts.yaml`.**
- `test/`:
  - `test_vector_agent.py`: Contains unit tests for the agent suite (using pytest).
  - `test_normal.py` & `test_stream.py`: Python CLI scripts to test the classic blocking API and the real-time Server-Sent Events (SSE) streaming API.
- `utilities/`: 
  - `ingest_files.py`: A robust ETL script with batch processing to extract, chunk, and ingest documents into ChromaDB. Includes hierarchical OpenTelemetry tracing.
  - `ingestion_state.json`: *(Auto-generated)* State file created after running the ingestion script. It tracks the MD5 hashes of processed files to prevent redundant ingestions.
- `Dockerfile`: Containerization setup for this microservice.
- `docker-compose.db.yaml`: Isolated infrastructure configuration for ChromaDB, Redis Stack servers, and Arize Phoenix telemetry.


## Features

- **Semantic Routing (LangGraph)**: Automatically analyzes the user's intent and routes the query to the correct vector collection (e.g., Game of Thrones, Harry Potter, Pokédex).
- **Configuration-Driven**: Adding a new knowledge base requires zero Python code changes. Just create a folder in `data/` and add its exact name to `prompts.yaml` along with its persona.
- **Data Privacy Shield (PII Anonymization)**: Dual-layer firewall powered by Microsoft Presidio and spaCy. It intercepts, detects, and masks sensitive data (like IPs or API keys) from user prompts before sending them to the LLM, ensuring enterprise-grade compliance.
- **Retrieval-Augmented Generation (RAG)**: Leverages ChromaDB for high-speed similarity search, ensuring the LLM only answers based on your private contextual data.
- **Real-Time Streaming (SSE)**: Hybrid API architecture offering both classic blocking responses and Server-Sent Events (SSE) streaming for real-time, token-by-token LLM generation, drastically reducing Time-to-First-Token (TTFT) for long responses.
- **Anti-Hallucination Guardrails**: Strict system prompting ensures the agent admits when it doesn't know the answer instead of fabricating information.
- **Session Isolation & Contextual Memory**: Integrates Redis with LangGraph to support multi-turn conversations using `session_id`.
- **Intelligent Batch Ingestion**: Features an optimized ETL pipeline that uses MD5 hashing to detect file changes. It only processes new or modified documents and automatically deletes obsolete vectors before updating, preventing data duplication and saving LLM token costs.
- **FastAPI integration**: Clean and fast API endpoints with Swagger UI documentation.
- **Optimized Resource Management**: Employs the Singleton design pattern for the Vector Engine, preventing memory leaks and connection exhaustion during high-concurrency loads.
- **Full Observability & Telemetry**: Integrated with OpenTelemetry and Arize Phoenix to trace LangGraph executions, monitor LLM latency/costs, and capture hierarchical (parent/child) spans during batch document ingestion.


## API Endpoints

- `GET /health`: Health check.
- `POST /ask-rag`: (Standard/Blocking) Send a natural language question to get the routed database, retrieved context chunks, and the final generated answer in a single JSON payload.
- `POST /ask-rag-stream`: (Streaming) Sends the query and returns a real-time stream of server-sent events, delivering the routed DB metadata first, followed by the LLM response token-by-token.

### Example Request

```json
{
  "question": "¿Qué animal descubren los hijos de Eddard Stark en su viaje de vuelta a Invernalia?",
  "session_id": "sesion_prueba_1"
}
```


## Running the Use Case

1. Configure your `.env` file in the root directory.
2. Spin up the isolated database and telemetry infrastructure (ChromaDB, Redis Stack, and Arize Phoenix):
  ```bash
  docker compose -f use_cases/vector_agent/docker-compose.db.yaml up -d
  ```
3. Ingest the documents into the vector database (Run this locally to populate ChromaDB)
  ```bash
  python use_cases/vector_agent/utilities/ingest_files.py
  ```
4. Run using Docker Compose:
   ```bash
   docker compose up --build -d vector-agent
   ```
5. The API will be available at http://localhost:8002/docs
*Note: Swagger UI does not perfectly render Server-Sent Events (SSE). To experience the real-time typewriter effect of the `/ask-rag-stream` endpoint, use the provided scripts in the `test/` folder (`python use_cases/vector_agent/test/test_stream.py`).*


## Running Tests

**The API endpoint tests are currently coupled to the default demonstration configuration (got_vector, pokedex_vector). If you clone this repository and modify config/prompts.yaml to fit your own business use case, you must update the assertions in test_vector_agent.py to match your new domains.**

### 1. Automated Testing (Pytest)
The test suite uses a hybrid strategy of `unittest.mock` and Pytest fixtures, meaning it does not consume LLM tokens, executes in seconds, and runs perfectly even if the database is completely empty.

To run the automated test suite and verify the integrity of the agent's logic, memory, and PII shields, run:
  ```bash
  docker compose run --rm vector-agent pytest use_cases/vector_agent/test/
  ```

### 2. Manual API Testing (Blocking vs Streaming)
To experience the difference between the classic REST approach and the new real-time architecture, use the provided test scripts:

**Standard Blocking API:** Sends a query and waits for the entire LLM generation to finish before returning the complete JSON payload.
  ```bash
  python use_cases/vector_agent/test/test_normal.py
  ```

**Real-Time Streaming (SSE):** Sends a query and immediately starts yielding tokens as they are generated by Azure OpenAI, creating a typewriter effect.
  ```bash
  python use_cases/vector_agent/test/test_stream.py
  ```


## Observability & Telemetry

This system is fully instrumented with `OpenTelemetry` and uses `Arize Phoenix` as the central telemetry collector to monitor the AI infrastructure. 

To access the Observability Dashboard, open your browser and navigate to:
`http://localhost:6006`

Inside the dashboard, you can audit:
- **LangGraph Traces:** Visualize the exact path the Supervisor node took to route the query to the specific expert agent.
- **LLM Metrics:** Track latency, execution times, and token usage costs for Azure OpenAI.
- **Ingestion Profiling:** View hierarchical (parent/child) spans of the `ingest_files.py` script to identify bottlenecks during large document batch processing.