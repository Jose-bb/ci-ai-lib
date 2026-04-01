import os
import sys
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Any

# Adding the root to sys.path to allow imports from llm_interfaces
# Now it's 3 levels up: src -> sql_agent -> use_cases -> root
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.append(ROOT_DIR)

from use_cases.sql_agent.src.sql_agent import SQLAgent

app = FastAPI(title="SQL Agent API", version="1.0.0")


# We initialize the agent once at startup, not on every request.
# This prevents reading the DB schema repeatedly.
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/tienda_prueba.sqlite'))
sql_agent = SQLAgent(db_path=DB_PATH)

class SQLQueryRequest(BaseModel):
    """SQLQueryRequest class defines the schema for the SQL Agent request."""
    question: str

class SQLQueryResponse(BaseModel):
    """SQLQueryRequest class defines the schema for the outgoing SQL Agent response."""
    question: str
    generated_sql: str
    data: List[Any]
    error: Optional[str] = None

@app.post("/ask-sql", response_model=SQLQueryResponse)
async def ask_sql(request: SQLQueryRequest):
    """
    Exposes an endpoint to translate natural language to SQL and execute it.

    Args:
        request (SQLQueryRequest): The request containing the natural language question.

    Returns:
        dict: The agent's response including the SQL and fetched data.
    """
    try:
        result = sql_agent.process_question(user_question=request.question)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/health")
async def health():
    """Health check for the SQL Agent"""
    return {"status": "ok", "agent": "SQLAgent up and running"}