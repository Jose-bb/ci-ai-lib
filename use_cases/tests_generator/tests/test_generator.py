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
def test_3_endpoint_success(mock_graph_run):
    """Test 3: Verifies the FastAPI endpoint returns a valid ZIP file on success."""
    # Bypasses the graph logic entirely to strictly test the API response structure
    mock_graph_run.return_value = {
        "error": None,
        "test_plan": "# API Test Plan",
        "generated_tests": "def test_api():\n    pass"
    }
    
    zip_bytes = create_dummy_zip("math_ops.py", "def sub(a, b):\n    return a - b")
    
    # Simulate a multipart/form-data file upload
    response = client.post(
        "/generate-tests-from-zip",
        files={"file": ("dummy_project.zip", zip_bytes, "application/zip")}
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert "attachment; filename=QA_suite_dummy_project.zip" in response.headers["content-disposition"]
    
    # Verify the contents of the downloaded ZIP in memory
    downloaded_zip = zipfile.ZipFile(io.BytesIO(response.content))
    zip_files = downloaded_zip.namelist()
    
    assert "test_plan_dummy_project.md" in zip_files
    assert "test_dummy_project.py" in zip_files
    
    assert downloaded_zip.read("test_plan_dummy_project.md").decode("utf-8") == "# API Test Plan"
    assert downloaded_zip.read("test_dummy_project.py").decode("utf-8") == "def test_api():\n    pass"


def test_4_endpoint_invalid_file_extension():
    """Test 4: Verifies the FastAPI endpoint rejects non-ZIP files early."""
    # Simulating uploading a .txt file instead of a .zip
    response = client.post(
        "/generate-tests-from-zip",
        files={"file": ("dummy_project.txt", b"plain text content", "text/plain")}
    )
    
    # Expecting a Fail-Fast 400 Bad Request
    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded file must be a .zip archive."


@patch('use_cases.tests_generator.src.main.generator_agent.run')
def test_5_endpoint_syntax_error(mock_graph_run):
    """Test 5: Verifies the FastAPI endpoint returns a 400 Bad Request on syntax errors."""
    # Simulates the graph catching a syntax error during the parsing phase
    mock_graph_run.return_value = {
        "error": "Failed to parse 'math_ops.py'. Syntax error: invalid syntax",
        "test_plan": None,
        "generated_tests": None
    }
    
    zip_bytes = create_dummy_zip("math_ops.py", "def sub(a, b) return a - b")
    
    response = client.post(
        "/generate-tests-from-zip",
        files={"file": ("broken_project.zip", zip_bytes, "application/zip")}
    )
    
    assert response.status_code == 400
    assert "Syntax error" in response.json()["detail"]