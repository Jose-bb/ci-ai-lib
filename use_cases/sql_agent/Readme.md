# Multi-Agent Hybrid DB Router Use Case (V3)

This use case provides a FastAPI endpoint that acts as an intelligent, multi-agent hybrid database router. Powered by LangGraph, SQLAlchemy, and PyMongo, it evaluates natural language questions, routes them to the appropriate database based on a YAML configuration, translates the intent into valid queries (supporting SQLite, PostgreSQL, and MongoDB), and safely executes them.

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
- `docker-compose.db.yaml`: Isolated infrastructure configuration for PostgreSQL and MongoDB servers.

## Features

- **Dynamic Routing (LangGraph)**: Automatically analyzes the user's intent and routes the query to the correct DB (e.g., Store, HR, Logistics).
- **Configuration-Driven**: Adding a new database requires zero Python code changes; it is entirely managed via `prompts.yaml`.
- **Multi-Paradigm Generation**: Converts user questions into raw SQL strings or PyMongo filter dictionaries (JSON) using AI.
- **Dynamic Schema Awareness**: Dynamically reads database schemas (using inspectors for SQL and document sampling for NoSQL) to ensure accurate queries and prevent AI hallucinations.
- **Security First**: Built-in Python shields prevent destructive queries. SQL execution blocks everything except `SELECT` and `WITH`, while NoSQL limits query sizes and prevents data mutation.
- **Robust Error Handling**: Safely catches DB exceptions and routing failures, returning standard HTTP error codes (e.g., 400 Bad Request).
- **FastAPI integration**: Clean and fast API endpoints.

## API Endpoints

- `GET /health`: Health check.
- `POST /ask-db`: Send a natural language question to get the routed database, generated query/filter, and fetched data.

### Example Request

```json
{
  "question": "What is the budget for the Black Friday campaign and where do its leads come from?"
}
```

## Running the Use Case

1. Configure your `.env` file in the root directory.
2. Spin up the isolated database infrastructure (PostgreSQL & MongoDB):
  ```bash
  docker compose -f use_cases/sql_agent/docker-compose.db.yaml up -d
  ```
3. Generate the local databases using the scripts in utilities/ if you haven't already.
4. Run using Docker Compose:
   ```bash
   docker-compose up sql-agent --build
   ```
5. The API will be available at http://localhost:8001/docs

## Running Tests

To run the automated test suite and verify the integrity of the agent's logic and security shields, run the following command from the root directory:
    ```bash
   docker compose run --rm sql-agent pytest use_cases/sql_agent/test/
   ```