FROM python:3.11-slim

WORKDIR /app

COPY use_cases/a2a_protocols/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all repository content
COPY . .

# Ensure that the workspace where agents will write temporary code has the necessary permissions
RUN mkdir -p /app/use_cases/a2a_protocols/workspace && chmod -R 777 /app/use_cases/a2a_protocols/workspace

# Set PYTHONPATH to root of the repository
ENV PYTHONPATH=/app

# Expose the port
EXPOSE 8000

# Command to run the fastapi application from the new src location
CMD ["uvicorn", "use_cases.a2a_protocols.src.main:app", "--host", "0.0.0.0", "--port", "8000"]