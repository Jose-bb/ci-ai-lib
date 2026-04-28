import os
import sys
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Any

# Adding the root to sys.path to allow imports from llm_interfaces
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from use_cases.vector_agent.src.supervisor import SupervisorGraph

app = FastAPI(title="Vector RAG Agent API", version="1.0.0")

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../config/prompts.yaml'))
supervisor = SupervisorGraph(config_path=CONFIG_PATH)

class QueryRequest(BaseModel):
    """QueryRequest class defines the schema for the request."""
    question: str
    session_id: str = "default_session"

class QueryResponse(BaseModel):
    """QueryResponse class defines the schema for the outgoing response."""
    question: str
    routed_db: Optional[str] = None
    retrieved_context: Optional[Any] = None 
    data: Any
    error: Optional[str] = None

@app.post("/ask-rag", response_model=QueryResponse)
async def ask_rag(request: QueryRequest):
    """Main endpoint. Routes the natural language question through the RAG workflow."""
    try:
        state = supervisor.run(user_question=request.question, session_id=request.session_id)
        
        # Catch routing failures
        if state.get("error"):
            raise HTTPException(status_code=400, detail=state["error"])

        agent_result = state.get("result", {})

        return {
            "question": state["question"],
            "routed_db": state.get("selected_db"),
            "retrieved_context": agent_result.get("context"),
            "data": agent_result.get("data")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/health")
async def health():
    """Health check for the Vector RAG API."""
    return {"status": "ok", "agent": "Vector RAG Supervisor up and running"}