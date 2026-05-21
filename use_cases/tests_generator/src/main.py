import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from use_cases.tests_generator.src.generator_graph import TestsGeneratorGraph

app = FastAPI(title="Tests Generator API", version="1.0.0")

class GenerationRequest(BaseModel):
    """Pydantic model for the incoming request payload."""
    source_code: str
    module_name: str

# Initialize the graph once at startup to avoid recompiling on every request
generator_agent = TestsGeneratorGraph()

@app.post("/generate-tests")
def generate_tests_endpoint(request: GenerationRequest):
    """Endpoint to process Python source code and return a test plan and generated tests."""
    try:
        result_state = generator_agent.run(source_code=request.source_code)
        
        if result_state.get("error"):
            raise HTTPException(status_code=500, detail=result_state["error"])
            
        return {
            "status": "success",
            "module_tested": request.module_name,
            "test_plan": result_state.get("test_plan"),
            "generated_code": result_state.get("generated_tests")
        }
    except HTTPException:
        raise    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@app.get("/health")
def health():
    """Health check for the API."""
    return {"status": "ok", "agent": "Generator Agent up and running"}