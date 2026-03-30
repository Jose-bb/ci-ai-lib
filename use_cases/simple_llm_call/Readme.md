# Simple LLM Call Use Case

This use case provides a simple FastAPI endpoint to interact with multiple LLM providers (Azure OpenAI, Gemini) through a unified interface.

## Project Structure

- `src/`: Contains the FastAPI application logic.
- `test/`: Contains unit tests for the use case.
- `Dockerfile`: Containerization setup for this specific use case.

## Features

- **Multi-provider support**: Switch between Azure OpenAI and Gemini via configuration or request parameters.
- **Unified interface**: Both providers adhere to the same `LLMInterface`.
- **FastAPI integration**: Clean and fast API endpoints.

## API Endpoints

- `GET /health`: Health check.
- `POST /chat`: Send a list of messages to the configured LLM.

### Example Request

```json
{
  "messages": [{"role": "user", "content": "Explain quantum physics in one sentence."}],
  "model": "gpt-4",
  "provider": "azure_openai"
}
```

## Running the Use Case

1. Configure your `.env` file in the root directory.
2. Run using Docker Compose:
   ```bash
   docker-compose up simple-llm-call
   ```
