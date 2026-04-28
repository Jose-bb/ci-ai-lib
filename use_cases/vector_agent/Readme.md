# Multi-Agent Hybrid DB Router with PII Privacy & Redis Memory (V5)

This use case provides a FastAPI endpoint that acts as an intelligent, multi-agent hybrid database router. Powered by LangGraph, SQLAlchemy, PyMongo, Microsoft Presidio, and Redis Stack, it evaluates natural language questions, routes them to the appropriate database based on a YAML configuration, translates the intent into valid queries, safely executes them, recursively anonymizes sensitive data, and maintains persistent conversational memory for multi-turn context.

## Project Structure

- `config/`: Contains `prompts.yaml`, the core configuration driving the LLM rules and database routing logic for both SQL and NoSQL targets.
- `src/`: 
  - `main.py`: FastAPI application entry point.
  - `supervisor.py`: LangGraph orchestrator that routes user intent to the correct semantic domain.
  - `base_agent.py`: Universal worker that extracts schemas and requests the exact query structure needed (SQL string or JSON dictionary).
  - `db_engines.py`: Secure execution engine capable of handling tabular data (SQLAlchemy) and nested document data (PyMongo).
- `data/`: Contains the local SQLite databases (`tienda_prueba.sqlite`, `recursos_humanos.sqlite`, `logistica.sqlite`).
- `test/`: Contains unit tests for the agent suite (using pytest).
- `utilities/`: Python scripts to generate and populate databases, including relational DBs and NoSQL collections (e.g., `create_mongo_logs.py`).
- `Dockerfile`: Containerization setup for this microservice.
- `docker-compose.db.yaml`: Isolated infrastructure configuration for PostgreSQL, MongoDB, and Redis Stack servers.

## Features

- **Dynamic Routing (LangGraph)**: Automatically analyzes the user's intent and routes the query to the correct DB (e.g., Store, HR, Logistics).
- **Configuration-Driven**: Adding a new database requires zero Python code changes; it is entirely managed via `prompts.yaml`.
- **Multi-Paradigm Generation**: Converts user questions into raw SQL strings or PyMongo filter dictionaries (JSON) using AI.
- **Dynamic Schema Awareness**: Dynamically reads database schemas (using inspectors for SQL and document sampling for NoSQL) to ensure accurate queries and prevent AI hallucinations.
- **Session Isolation**: Supports multi-tenant conversations using `session_id`, allowing the backend to handle thousands of independent user sessions simultaneously without data bleed.
- **Context-Aware Reasoning**: The LangGraph supervisor leverages historical state to seamlessly resolve ambiguous follow-up questions (e.g., "What was the name of the previous client?").
- **Deterministic Key Masking:** Instantly redacts highly sensitive keys (`password`, `token`, `api_key`) before they even reach the AI.
- **Probabilistic NLP Masking:** Integrates Microsoft Presidio and spaCy NLP to recursively scan and anonymize sensitive Personal Identifiable Information (like IPs, Credit Cards, and National IDs) hiding in free text across any depth of nested SQL or NoSQL results (GDPR ready).
- **Security First**: Built-in Python shields prevent destructive queries. SQL execution blocks everything except `SELECT` and `WITH`, while NoSQL limits query sizes and prevents data mutation.
- **FastAPI integration**: Clean and fast API endpoints.

## API Endpoints

- `GET /health`: Health check.
- `POST /ask-db`: Send a natural language question to get the routed database, generated query/filter, and the scrubbed, privacy-safe data.

### Example Request

```json
{
  "question": "Show me the logs that threw a CRITICAL error.",
  "session_id": "user_session_123"
}
```

## Running the Use Case

1. Configure your `.env` file in the root directory.
2. Spin up the isolated database infrastructure (PostgreSQL, MongoDB & Redis Stack):
  ```bash
  docker compose -f use_cases/sql_agent/docker-compose.db.yaml up -d
  ```
3. Generate the local databases using the scripts in utilities/ if you haven't already.
4. Run using Docker Compose:
   ```bash
   docker-compose up --build -d sql-agent
   ```
5. The API will be available at http://localhost:8001/docs

## Running Tests

To run the automated test suite and verify the integrity of the agent's logic and security shields, run the following command from the root directory:
    ```bash
   docker compose run --rm sql-agent pytest use_cases/sql_agent/test/
   ```