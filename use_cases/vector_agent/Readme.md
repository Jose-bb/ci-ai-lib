# Multi-Agent VecDB Router with PII Privacy & Redis Memory (V1)

This use case provides a FastAPI endpoint that acts as an intelligent, multi-domain Retrieval-Augmented Generation (RAG) system. Powered by LangGraph, ChromaDB, Azure OpenAI, Microsoft Presidio, and Redis, it evaluates natural language questions, routes them to the appropriate knowledge base based on a YAML configuration, performs semantic search to retrieve relevant context, and generates highly accurate, hallucination-free answers while maintaining persistent conversational memory for multi-turn context.

## Project Structure

- `config/`: Contains `prompts.yaml`, the core configuration driving the LLM rules, and collection routing logic.
- `src/`: 
  - `main.py`: FastAPI application entry point.
  - `supervisor.py`: LangGraph orchestrator that routes user intent to the correct knowledge domain and manages conversational state with Redis.
  - `rag_agent.py`: Worker agent that injects retrieved context into prompts to generate grounded, natural language answers.
  - `vector_engine.py`: Engine responsible for embedding text and interacting with ChromaDB for similarity search.
- `data/`: Contains the raw knowledge files (TXT, CSV, PDF) organized by domain.
- `test/`: Contains unit tests for the agent suite (using pytest).
- `utilities/`: Contains `ingest_files.py`, a robust ETL script with batch processing to extract, chunk, and ingest documents into ChromaDB.
- `Dockerfile`: Containerization setup for this microservice.
- `docker-compose.db.yaml`: Isolated infrastructure configuration for ChromaDB, and Redis Stack servers.

## Features

- **Semantic Routing (LangGraph)**: Automatically analyzes the user's intent and routes the query to the correct vector collection (e.g., Game of Thrones, Harry Potter, Pokédex).
- **Configuration-Driven**: Adding a new knowledge base or changing an agent's persona requires zero Python code changes; it is entirely managed via `prompts.yaml`.
- **Retrieval-Augmented Generation (RAG)**: Leverages ChromaDB for high-speed similarity search, ensuring the LLM only answers based on your private contextual data.
- **Anti-Hallucination Guardrails**: Strict system prompting ensures the agent admits when it doesn't know the answer instead of fabricating information (e.g., "The ravens have brought no news on that matter").
- **Session Isolation & Contextual Memory**: Integrates Redis with LangGraph to support multi-turn conversations using `session_id`. The agent leverages historical state to seamlessly resolve ambiguous follow-up questions (e.g., "And who gets the white one?").
- **Resilient Batch Ingestion**: Features an optimized ETL pipeline that chunks large documents and uploads them to Azure/ChromaDB in manageable batches to prevent API rate limits and 500 Internal Server Errors.
- **FastAPI integration**: Clean and fast API endpoints with Swagger UI documentation.

## API Endpoints

- `GET /health`: Health check.
- `POST /ask-rag`: Send a natural language question to get the routed database, retrieved context chunks, and the final generated answer.

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

## Running Tests

To run the automated test suite and verify the integrity of the agent's logic and security shields, run the following command from the root directory:
    ```bash
   docker compose run --rm vector-agent pytest use_cases/vector_agent/test/
   ```