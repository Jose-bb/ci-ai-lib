import os
import sys
import io
import zipfile
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Ensure the root directory is accessible for absolute imports
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from use_cases.tests_generator.src.main import app
from use_cases.tests_generator.src.generator_graph import QAGeneratorGraph

client = TestClient(app)

@pytest.fixture
def mock_llm_factory():
    """Fixture to mock the LLMFactory and avoid real Azure OpenAI API calls."""
    with patch("use_cases.tests_generator.src.generator_graph.LLMFactory.get_llm") as mock_get_llm:
        mock_llm_instance = MagicMock()
        mock_get_llm.return_value = mock_llm_instance
        # Yield passes the mock to the test and safely tears it down afterward
        yield mock_llm_instance


def create_dummy_zip(file_name="main.py", content="def add(a, b):\n    return a + b") -> bytes:
    """Helper function to create a zip file in memory for testing the endpoint."""
    memory_zip = io.BytesIO()
    with zipfile.ZipFile(memory_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(file_name, content)
    return memory_zip.getvalue()


def test_1_successful_generation(mock_llm_factory):
    """Test 1: Graph successfully processes a valid project files dictionary."""
    # side_effect acts as a sequence: returns the plan first, then the code string
    mock_llm_factory.invoke.side_effect = [
        "# Global Mocked Test Plan",
        "def test_mock():\n    assert True"
    ]
    
    graph = QAGeneratorGraph()
    project_files = {"src/main.py": "def add(a, b):\n    return a + b"}
    
    result = graph.run(project_files=project_files)
    
    assert result["error"] is None
    assert result["test_plan"] == "# Global Mocked Test Plan"
    assert result["generated_tests"] == "def test_mock():\n    assert True"
    # Validates that both the planner and coder nodes executed
    assert mock_llm_factory.invoke.call_count == 2


def test_2_syntax_error_handling(mock_llm_factory):
    """Test 2: Graph gracefully handles invalid Python code and halts execution."""
    graph = QAGeneratorGraph()
    project_files = {"src/invalid.py": "def add(a, b) return a + b"}
    
    result = graph.run(project_files=project_files)
    
    assert result["error"] is not None
    assert "Syntax error" in result["error"]
    assert result["test_plan"] is None
    assert result["generated_tests"] is None
    mock_llm_factory.invoke.assert_not_called()


@patch('use_cases.tests_generator.src.main.generator_agent.run')
def test_3_async_zip_endpoint_success(mock_graph_run):
    """Test 3: Verifies the async flow for ZIP upload (202 Accepted -> 200 OK with ZIP)."""
    mock_graph_run.return_value = {
        "error": None,
        "test_plan": "# API Test Plan",
        "generated_tests": "def test_api():\n    pass"
    }
    
    zip_bytes = create_dummy_zip("math_ops.py", "def sub(a, b):\n    return a - b")
    
    # POST step: Queue the task
    response_post = client.post(
        "/generate-tests-from-zip",
        files={"file": ("dummy_project.zip", zip_bytes, "application/zip")}
    )
    assert response_post.status_code == 202
    assert "task_id" in response_post.json()
    task_id = response_post.json()["task_id"]
    
    # GET step: Retrieve the results
    response_get = client.get(f"/status/{task_id}")
    
    assert response_get.status_code == 200
    assert response_get.headers["content-type"] == "application/zip"
    assert "attachment;" in response_get.headers["content-disposition"]
    
    downloaded_zip = zipfile.ZipFile(io.BytesIO(response_get.content))
    zip_files = downloaded_zip.namelist()
    
    assert any(f.endswith(".md") for f in zip_files)
    assert any(f.endswith(".py") for f in zip_files)


def test_4_endpoint_invalid_file_extension():
    """Test 4: Verifies the FastAPI endpoint rejects non-ZIP files early."""
    # Simulating uploading a .txt file instead of a .zip
    response = client.post(
        "/generate-tests-from-zip",
        files={"file": ("dummy_project.txt", b"plain text content", "text/plain")}
    )
    
    # Expecting a Fail-Fast 400 Bad Request
    assert response.status_code == 400
    assert "Uploaded file must be a .zip archive." in response.json()["detail"]


@patch('use_cases.tests_generator.src.main.generator_agent.run')
def test_5_async_endpoint_syntax_error(mock_graph_run):
    """Test 5: Verifies the status endpoint returns a 400 Bad Request on syntax errors."""
    mock_graph_run.return_value = {
        "error": "Failed to parse 'math_ops.py'. Syntax error: invalid syntax",
        "test_plan": None,
        "generated_tests": None
    }
    
    zip_bytes = create_dummy_zip("math_ops.py", "def sub(a, b) return a - b")
    
    response_post = client.post(
        "/generate-tests-from-zip",
        files={"file": ("broken_project.zip", zip_bytes, "application/zip")}
    )
    assert response_post.status_code == 202
    task_id = response_post.json()["task_id"]
    
    response_get = client.get(f"/status/{task_id}")
    
    # Validate that the endpoint returns 400 and contains the message
    assert response_get.status_code == 400
    assert "Syntax error" in response_get.text


@patch('use_cases.tests_generator.src.main.GitExtractor.extract_repository')
@patch('use_cases.tests_generator.src.main.generator_agent.run')
def test_6_async_git_endpoint_success(mock_graph_run, mock_git_extract):
    """Test 6: Verifies the async flow for GitHub URL processing with an optional token."""
    mock_git_extract.return_value = {"src/main.py": "def dummy(): pass"}
    mock_graph_run.return_value = {
        "error": None,
        "test_plan": "# Git Test Plan",
        "generated_tests": "def test_git():\n    pass"
    }
    
    response_post = client.post(
        "/generate-tests-from-git",
        json={
            "repo_url": "https://github.com/dummy/repo.git",
            "github_token": "valid_token_123"
        }
    )
    
    assert response_post.status_code == 202
    task_id = response_post.json()["task_id"]
    
    response_get = client.get(f"/status/{task_id}")
    assert response_get.status_code == 200
    assert response_get.headers["content-type"] == "application/zip"


@patch('use_cases.tests_generator.src.main.GitExtractor.extract_repository')
def test_7_async_git_endpoint_failure(mock_git_extract):
    """Test 7: Verifies the async task fails gracefully for invalid Git repositories."""
    # Simulate that the extraction fails
    mock_git_extract.side_effect = RuntimeError("Failed to clone repository. Error: Not found")
    
    # The POST accepts the request quickly (202)
    response_post = client.post(
        "/generate-tests-from-git",
        json={"repo_url": "https://github.com/invalid/repo.git"}
    )
    assert response_post.status_code == 202
    task_id = response_post.json()["task_id"]
    
    # The GET to status reveals that the background task failed
    response_get = client.get(f"/status/{task_id}")
    assert response_get.status_code == 400
    assert "Failed to clone repository" in response_get.text


@patch('use_cases.tests_generator.src.main.GitExtractor.extract_repository')
def test_8_async_git_token_masking_on_error(mock_git_extract):
    """Test 8: Verifies that Personal Access Tokens are securely masked in error messages."""
    secret_token = "super_secret_pat_999"
    
    # Simulate a git clone failure where the raw standard error outputs the injected URL
    mock_git_extract.side_effect = Exception(f"fatal: repository 'https://x-access-token:{secret_token}@github.com/dummy/private.git/' not found")
    
    response_post = client.post(
        "/generate-tests-from-git",
        json={
            "repo_url": "https://github.com/dummy/private.git",
            "github_token": secret_token
        }
    )
    assert response_post.status_code == 202
    task_id = response_post.json()["task_id"]
    
    response_get = client.get(f"/status/{task_id}")
    assert response_get.status_code == 400
    
    error_msg = response_get.json()["error"]
    
    # Assert that the token was effectively scrubbed from the exposed error string
    assert secret_token not in error_msg
    assert "***MASKED_TOKEN***" in error_msg