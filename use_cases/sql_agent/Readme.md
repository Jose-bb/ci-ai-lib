# SQL Agent Use Case

This use case provides a FastAPI endpoint that acts as an intelligent SQL Agent. It translates natural language questions into valid SQLite queries and executes them against a local database.

## Project Structure

- `src/`: Contains the FastAPI application logic and the `SQLAgent` class.
- `data/`: Contains the local SQLite database (`tienda_prueba.sqlite`).
- `test/`: Contains unit tests for the agent.
- `utilities/`: Contains scripts to generate or reset the local database.
- `Dockerfile`: Containerization setup for this microservice.

## Features

- **Natural Language to SQL**: Converts user questions into SQL using LLMs.
- **Autonomous Execution**: Automatically runs the generated query and returns the fetched data.
- **Schema Awareness**: Dynamically reads the database schema to ensure accurate queries.
- **FastAPI integration**: Clean and fast API endpoints.

## API Endpoints

- `GET /health`: Health check.
- `POST /ask-sql`: Send a natural language question to get SQL and data.

### Example Request

```json
{
  "question": "Which customers live in Madrid?"
}
```

## Running the Use Case

1. Configure your `.env` file in the root directory.
2. Generate the local database using the script in utilities/ if you haven't already.
3. Run using Docker Compose:
   ```bash
   docker-compose up sql-agent --build
   ```
4. The API will be available at http://localhost:8001/docs