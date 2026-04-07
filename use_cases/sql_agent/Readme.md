# Multi-Agent SQL Router Use Case (V2)

This use case provides a FastAPI endpoint that acts as an intelligent, multi-agent database router. Powered by LangGraph and SQLAlchemy, it evaluates natural language questions, routes them to the appropriate database based on a YAML configuration, translates the intent into valid queries (supporting both SQLite and PostgreSQL), and safely executes them.

## Project Structure

- `config/`: Contains `prompts.yaml`, the core configuration driving the LLM rules and database routing logic.
- `src/`: 
  - `main.py`: FastAPI application entry point.
  - `supervisor.py`: LangGraph orchestrator that routes user intent.
  - `base_agent.py`: Universal worker that generates the SQL based on dynamic schemas.
  - `db_engines.py`: Secure execution engine powered by SQLAlchemy.
- `data/`: Contains the local SQLite databases (`tienda_prueba.sqlite`, `recursos_humanos.sqlite`, `logistica.sqlite`).
- `test/`: Contains unit tests for the agent suite (using pytest).
- `utilities/`: Python scripts to generate and populate both local and remote databases.
- `Dockerfile`: Containerization setup for this microservice.
- `docker-compose.db.yaml`: Isolated infrastructure configuration for the PostgreSQL server.

## Features

- **Dynamic Routing (LangGraph)**: Automatically analyzes the user's intent and routes the query to the correct DB (e.g., Store, HR, Logistics).
- **Configuration-Driven**: Adding a new database requires zero Python code changes; it is entirely managed via `prompts.yaml`.
- **Natural Language to SQL**: Converts user questions into SQL using AI.
- **Schema Awareness**: Dynamically reads the database schema to ensure accurate queries and prevent hallucinations.
- **Security First**: Built-in Python shields prevent destructive queries (only `SELECT` and `WITH` statements are allowed).
- **Robust Error Handling**: Safely catches DB exceptions and routing failures, returning standard HTTP error codes (e.g., 400 Bad Request).
- **FastAPI integration**: Clean and fast API endpoints.

## API Endpoints

- `GET /health`: Health check.
- `POST /ask-sql`: Send a natural language question to get the routed database, generated SQL, and fetched data.

### Example Request

```json
{
  "question": "What is the budget for the Black Friday campaign and where do its leads come from?"
}
```

## Running the Use Case

1. Configure your `.env` file in the root directory.
2. Spin up the isolated PostgreSQL infrastructure:
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