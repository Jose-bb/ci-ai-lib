import os
import sys
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Any

# Adding the root to sys.path to allow imports from llm_interfaces
# Now it's 3 levels up: src -> sql_agent -> use_cases -> root
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from use_cases.sql_agent.src.supervisor import SupervisorGraph

app = FastAPI(title="Multi-Agent DB API", version="2.0.0")

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../config/prompts.yaml'))
supervisor = SupervisorGraph(config_path=CONFIG_PATH)

class QueryRequest(BaseModel):
    """QueryRequest class defines the schema for the request."""
    question: str

class QueryResponse(BaseModel):
    """QueryRequest class defines the schema for the outgoing response."""
    question: str
    routed_db: Optional[str] = None
    data: Any
    error: Optional[str] = None

@app.post("/ask-sql", response_model=QueryResponse)
async def ask_sql(request: QueryRequest):
    """Main endpoint. Routes the natural language question through the LangGraph workflow."""
    try:
        state = supervisor.run(user_question=request.question)
        
        if state.get("error"):
            raise HTTPException(status_code=400, detail=state["error"])

        return {
            "question": state["question"],
            "routed_db": state.get("selected_db"),
            "data": state.get("result")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/health")
async def health():
    """Health check for the Multi-Agent API."""
    return {"status": "ok", "agent": "Multi-Agent Supervisor up and running"}