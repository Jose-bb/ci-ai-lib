FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (Git)
RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

# Copy the specific requirements for the tests generator
COPY use_cases/tests_generator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all repository content
COPY . .

# Set PYTHONPATH to the root of the repository
ENV PYTHONPATH=/app

# Expose the API port
EXPOSE 8000

# Command to run the FastAPI application from the new src location
CMD ["uvicorn", "use_cases.tests_generator.src.main:app", "--host", "0.0.0.0", "--port", "8000"]