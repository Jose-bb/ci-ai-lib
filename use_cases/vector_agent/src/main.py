import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Any, List, Dict
from dotenv import load_dotenv

from phoenix.otel import register
from openinference.instrumentation.langchain import LangChainInstrumentor

load_dotenv()

# Telemetry must be initialized before creating the FastAPI app to capture all traces
tracer_provider = register()
LangChainInstrumentor().instrument(tracer_provider=tracer_provider)

# Ensure the root directory is in the path to allow absolute imports
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from use_cases.vector_agent.src.supervisor import SupervisorGraph

app = FastAPI(title="Vector RAG Agent API", version="3.0.0")

# Initialize the supervisor globally so it loads the catalog and Redis connection only once at startup
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../config/prompts.yaml'))
supervisor = SupervisorGraph(config_path=CONFIG_PATH)

class QueryRequest(BaseModel):
    """Schema for incoming RAG queries."""
    question: str = Field(..., description="The natural language question to ask the RAG agent.")
    session_id: str = Field(default="default_session", description="Unique ID to maintain conversational memory.")


class QueryResponse(BaseModel):
    """Schema for the outgoing RAG response."""
    question: str
    routed_db: Optional[str] = Field(default=None, description="The knowledge base selected by the router.")
    retrieved_context: Optional[List[Dict[str, Any]]] = Field(default=None, description="Chunks retrieved from the vector DB.")
    data: Optional[Any] = Field(default=None, description="The final generated answer or payload.")
    error: Optional[str] = None


@app.post("/ask-rag", response_model=QueryResponse)
def ask_rag(request: QueryRequest):
    """Routes the natural language question through the RAG workflow (Standard/Blocking)."""
    try:
        state = supervisor.run(user_question=request.question, session_id=request.session_id)
        
        # Catch explicit routing or execution failures
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


@app.post("/ask-rag-stream")
def ask_rag_stream(request: QueryRequest):
    """Routes the question and streams the response back token by token (Server-Sent Events)."""
    try:
        generator = supervisor.stream_run(
            user_question=request.question, 
            session_id=request.session_id
        )
        
        return StreamingResponse(generator, media_type="text/event-stream")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@app.get("/health")
def health():
    """Health check for the API."""
    return {"status": "ok", "agent": "Vector RAG Supervisor up and running"}