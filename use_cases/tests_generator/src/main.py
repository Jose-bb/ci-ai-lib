import os
import io
import zipfile
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import Response

from use_cases.tests_generator.src.generator_graph import QAGeneratorGraph
from use_cases.tests_generator.utilities.zip_extractor import ZipExtractor

app = FastAPI(title="Tests Generator API (V2)", version="2.0.0")

# Initialize the LangGraph globally to prevent compilation overhead
generator_agent = QAGeneratorGraph()

@app.post("/generate-tests-from-zip")
async def generate_tests_from_zip_endpoint(file: UploadFile = File(...)):
    """
    Endpoint to process a zipped Python project and return a downloadable ZIP 
    containing the global test plan and the pytest suite.
    """
    # Immediate validation
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Uploaded file must be a .zip archive.")

    try:
        # Extract the base name of the project without the .zip extension
        project_base_name = file.filename.replace(".zip", "")

        # Read the file bytes asynchronously into memory
        zip_bytes = await file.read()
        
        # Extract valid Python files using our utility
        project_files = ZipExtractor.extract_python_files(zip_bytes)
        
        if not project_files:
            raise HTTPException(status_code=400, detail="No valid Python files found in the provided ZIP.")

        # Trigger the LangGraph execution pipeline
        result_state = generator_agent.run(project_files=project_files)
        
        if result_state.get("error"):
            raise HTTPException(status_code=400, detail=result_state["error"])

        test_plan_content = result_state.get("test_plan", "")
        generated_code_content = result_state.get("generated_tests", "")

        # Create the output ZIP file in memory
        memory_zip = io.BytesIO()
        with zipfile.ZipFile(memory_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            # Add the Markdown test plan
            zf.writestr(f"test_plan_{project_base_name}.md", test_plan_content)
            # Add the Python test suite
            zf.writestr(f"test_{project_base_name}.py", generated_code_content)

        # Return the ZIP file as a downloadable response
        headers = {
            "Content-Disposition": f"attachment; filename=QA_suite_{project_base_name}.zip"
        }
        
        return Response(
            content=memory_zip.getvalue(),
            media_type="application/zip",
            headers=headers
        )

    except HTTPException:
        raise    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/health")
def health():
    """Health check for the API."""
    return {"status": "ok", "agent": "Generator Agent V2 up and running"}