import os
import sys
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional

# Adding the root to sys.path to allow imports from llm_interfaces
# Now it's 3 levels up: src -> simple_llm_call -> use_cases -> root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from llm_interfaces.factory import LLMFactory

app = FastAPI(title="Simple LLM Call Use Case")

class ChatRequest(BaseModel):
    '''
    ChatRequest class defines the schema for the chat endpoint request.
    '''
    messages: List[Dict[str, str]]
    model: str
    provider: Optional[str] = None

@app.post("/chat")
async def chat(request: ChatRequest):
    '''
    Exposes a simple LLM chat endpoint.

    Args:
        request (ChatRequest): The chat request containing messages and model.

    Returns:
        dict: The LLM response.
    '''
    try:
        llm = LLMFactory.get_llm(provider=request.provider)
        response = llm.invoke(messages=request.messages, model=request.model)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    '''
    Health check endpoint.

    Returns:
        dict: The health status.
    '''
    return {"status": "ok"}
