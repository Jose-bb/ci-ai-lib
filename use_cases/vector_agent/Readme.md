# Multi-Agent VecDB Router with PII Privacy, Redis Memory & SSE Streaming (V2)

This use case provides a FastAPI endpoint that acts as an intelligent, multi-domain Retrieval-Augmented Generation (RAG) system. Powered by LangGraph, ChromaDB, Azure OpenAI, Microsoft Presidio, and Redis, it evaluates natural language questions, routes them to the appropriate knowledge base based on a YAML configuration, performs semantic search to retrieve relevant context, and generates highly accurate, hallucination-free answers while maintaining persistent conversational memory for multi-turn context.

## Project Structure

- `config/`: Contains `prompts.yaml`, the core configuration driving the LLM rules, and collection routing logic.
- `src/`: 
  - `main.py`: FastAPI application entry point.
  - `supervisor.py`: LangGraph orchestrator that routes user intent to the correct knowledge domain and manages conversational state with Redis.
  - `rag_agent.py`: Worker agent that injects retrieved context into prompts to generate grounded, natural language answers.
  - `vector_engine.py`: Engine responsible for embedding text and interacting with ChromaDB for similarity search.
- `data/`: Contains the raw knowledge files (TXT, CSV, PDF) organized by domain. **The subfolder names inside this directory must exactly match the `collection_name` variables defined in your `prompts.yaml`.**
- `test/`: Contains unit tests for the agent suite (using pytest).
- `utilities/`: 
  - `ingest_files.py`: A robust ETL script with batch processing to extract, chunk, and ingest documents into ChromaDB.
  - `test_normal.py` & `test_stream.py`: Python CLI scripts to test the classic blocking API and the real-time Server-Sent Events (SSE) streaming API.
- `Dockerfile`: Containerization setup for this microservice.
- `docker-compose.db.yaml`: Isolated infrastructure configuration for ChromaDB, and Redis Stack servers.

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
2. Spin up the isolated database infrastructure (ChromaDB and Redis Stack):
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
*Note: Swagger UI does not perfectly render Server-Sent Events (SSE). To experience the real-time typewriter effect of the `/ask-rag-stream` endpoint, use the provided scripts in the `utilities/` folder (`python utilities/test_stream.py`).*

## Running Tests

**The API endpoint tests are currently coupled to the default demonstration configuration (got_vector, pokedex_vector). If you clone this repository and modify config/prompts.yaml to fit your own business use case, you must update the assertions in test_vector_agent.py to match your new domains.**

The test suite uses a hybrid strategy of `unittest.mock` and Pytest fixtures, meaning it does not consume LLM tokens, executes in seconds, and runs perfectly even if the database is completely empty.

To run the automated test suite and verify the integrity of the agent's logic, memory, and PII shields, run:
    ```bash
   docker compose run --rm vector-agent pytest use_cases/vector_agent/test/
   ```