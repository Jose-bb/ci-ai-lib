import os
import io
import uuid
import zipfile
from typing import Optional
from urllib.parse import urlparse
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel, HttpUrl

from use_cases.tests_generator.src.generator_graph import QAGeneratorGraph
from use_cases.tests_generator.utilities.zip_extractor import ZipExtractor
from use_cases.tests_generator.utilities.git_extractor import GitExtractor

app = FastAPI(title="Tests Generator API (V4)", version="4.0.0")

# Initialize LangGraph globally to prevent compilation overhead
generator_agent = QAGeneratorGraph()

# In-memory store for background tasks
tasks_store = {}

class GitGenerationRequest(BaseModel):
    repo_url: HttpUrl
    github_token: Optional[str] = None

def create_progress_callback(task_id: str):
    """
    Creates a callback function tied to a specific task_id.
    This will be passed into LangGraph to update the global state.
    """
    def callback(progress: int, message: str):
        if task_id in tasks_store:
            tasks_store[task_id]["progress"] = progress
            tasks_store[task_id]["message"] = message
    return callback


def generate_qa_artifacts(task_id: str, project_files: dict, project_base_name: str, callback=None):
    """Worker to run LangGraph and build the ZIP file in the background."""
    # Ensure we have a callback, either passed from the Git worker or created fresh for ZIPs
    if not callback:
        callback = create_progress_callback(task_id)

    try:
        # Trigger the LangGraph execution pipeline, passing the progress callback
        result_state = generator_agent.run(
            project_files=project_files, 
            progress_callback=callback
        )
        
        if result_state.get("error"):
            tasks_store[task_id] = {"status": "failed", "error": result_state["error"]}
            return

        callback(95, "Packaging files into ZIP archive...")

        # Create the output ZIP file in memory
        memory_zip = io.BytesIO()
        with zipfile.ZipFile(memory_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(f"test_plan_{project_base_name}.md", result_state.get("test_plan", ""))
            zf.writestr(f"test_{project_base_name}.py", result_state.get("generated_tests", ""))
        
        # Save result in memory and mark as completed
        tasks_store[task_id] = {
            "status": "completed",
            "progress": 100,
            "message": "Process completed! File ready for download.",
            "file_bytes": memory_zip.getvalue(),
            "filename": f"QA_suite_{project_base_name}.zip"
        }
        
    except Exception as e:
        tasks_store[task_id] = {"status": "failed", "error": str(e)}


def process_git_repository(task_id: str, repo_url: str, github_token: Optional[str], project_base_name: str):
    """Worker to handle Git cloning with optional PAT authentication."""
    callback = create_progress_callback(task_id)
    try:
        callback(5, "Cloning GitHub repository into memory...")
        project_files = GitExtractor.extract_repository(repo_url, github_token)
        
        if not project_files:
            tasks_store[task_id] = {"status": "failed", "error": "No valid Python files found."}
            return
        
        callback(10, "Repository cloned. Starting AI engine...")
        
        # Chain into the main QA generation logic, passing the existing callback down
        generate_qa_artifacts(task_id, project_files, project_base_name, callback)
        
    except Exception as e:
        error_msg = str(e)
        # Prevent PAT token leakage in error logs or API responses
        if github_token and github_token in error_msg:
            error_msg = error_msg.replace(github_token, "***MASKED_TOKEN***")
            
        tasks_store[task_id] = {"status": "failed", "error": error_msg}


@app.post("/generate-tests-from-zip")
async def generate_tests_from_zip_endpoint(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Accepts a ZIP, queues the QA generation, and returns a Task ID."""
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Uploaded file must be a .zip archive.")

    project_base_name = file.filename.replace(".zip", "")
    zip_bytes = await file.read()
    
    # Extract synchronously to fail fast if the ZIP is corrupted or empty
    try:
        project_files = ZipExtractor.extract_python_files(zip_bytes)
        if not project_files:
            raise HTTPException(status_code=400, detail="No valid Python files found.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Queue the background task with initial progress state
    task_id = str(uuid.uuid4())
    tasks_store[task_id] = {
        "status": "processing", 
        "progress": 0, 
        "message": "Queueing ZIP extraction task..."
    }
    background_tasks.add_task(generate_qa_artifacts, task_id, project_files, project_base_name)
    
    return JSONResponse(status_code=202, content={"task_id": task_id, "status": "processing"})


@app.post("/generate-tests-from-git")
async def generate_tests_from_git_endpoint(request: GitGenerationRequest, background_tasks: BackgroundTasks):
    """Accepts a Git URL (and optional PAT), queues repository cloning, and returns a Task ID."""
    parsed_url = urlparse(str(request.repo_url))
    path_parts = parsed_url.path.strip("/").split("/")
    project_base_name = path_parts[-1].replace(".git", "") if path_parts else "git_project"

    # Queue the background task with initial progress state
    task_id = str(uuid.uuid4())
    tasks_store[task_id] = {
        "status": "processing", 
        "progress": 0, 
        "message": "Queueing GitHub cloning task..."
    }
    background_tasks.add_task(process_git_repository, task_id, str(request.repo_url), request.github_token, project_base_name)
    
    return JSONResponse(status_code=202, content={"task_id": task_id, "status": "processing"})


@app.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """
    Checks the status of a task. 
    Returns the ZIP file directly if completed, or JSON with progress if still processing/failed.
    """
    task = tasks_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found or already downloaded.")

    if task["status"] == "processing":
        # Return the newly added progress tracking fields
        return {
            "task_id": task_id, 
            "status": "processing",
            "progress": task.get("progress", 0),
            "message": task.get("message", "Processing...")
        }
    
    if task["status"] == "failed":
        error_msg = task.get("error", "Unknown error")
        del tasks_store[task_id] # Clean up memory
        return JSONResponse(status_code=400, content={"task_id": task_id, "status": "failed", "error": error_msg})

    if task["status"] == "completed":
        file_bytes = task["file_bytes"]
        filename = task["filename"]
        
        # Prevent memory leak by removing the task once downloaded
        del tasks_store[task_id]
        
        headers = {"Content-Disposition": f"attachment; filename={filename}"}
        return Response(content=file_bytes, media_type="application/zip", headers=headers)


@app.get("/health")
def health():
    """Health check for the API."""
    return {"status": "ok", "agent": "Generator Agent V4 up and running"}