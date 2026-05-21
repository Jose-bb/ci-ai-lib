import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from use_cases.tests_generator.src.generator_graph import QAGeneratorGraph

app = FastAPI(title="Tests Generator API", version="1.0.0")

class GenerationRequest(BaseModel):
    """Pydantic model to enforce strict payload validation."""
    source_code: str
    module_name: str

class GenerationResponse(BaseModel):
    """Pydantic model defining the exact structure of a successful API response."""
    status: str
    module_tested: str
    test_plan: str
    generated_code: str

# Initialize the LangGraph globally to prevent compilation overhead on every HTTP request
generator_agent = QAGeneratorGraph()

@app.post("/generate-tests", response_model=GenerationResponse)
def generate_tests_endpoint(request: GenerationRequest):
    """Endpoint to process Python source code and return a test plan and generated tests."""
    try:
        # Trigger the LangGraph execution pipeline
        result_state = generator_agent.run(source_code=request.source_code)
        
        # Map syntax/parsing errors to a 400 Bad Request
        if result_state.get("error"):
            raise HTTPException(status_code=400, detail=result_state["error"])
            
        return {
            "status": "success",
            "module_tested": request.module_name,
            "test_plan": result_state.get("test_plan"),
            "generated_code": result_state.get("generated_tests")
        }

    except HTTPException:
        raise    
    except Exception as e:
        # Catch unexpected Python exceptions to prevent abrupt application crashes
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@app.get("/health")
def health():
    """Health check for the API."""
    return {"status": "ok", "agent": "Generator Agent up and running"}