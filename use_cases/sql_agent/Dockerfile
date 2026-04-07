FROM python:3.11-slim

WORKDIR /app

COPY use_cases/sql_agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all repository content
COPY . .

# Set PYTHONPATH to root of the repository
ENV PYTHONPATH=/app

# Expose the port
EXPOSE 8000

# Command to run the fastapi application from the new src location
CMD ["uvicorn", "use_cases.sql_agent.src.main:app", "--host", "0.0.0.0", "--port", "8000"]