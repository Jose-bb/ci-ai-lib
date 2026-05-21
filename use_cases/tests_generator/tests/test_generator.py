import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from use_cases.tests_generator.src.main import app
from use_cases.tests_generator.src.generator_graph import TestsGeneratorGraph

client = TestClient(app)

@pytest.fixture
def mock_llm_factory():
    """Fixture to mock the LLMFactory and avoid real Azure OpenAI API calls."""
    with patch("use_cases.tests_generator.src.generator_graph.LLMFactory.get_llm") as mock_get_llm:
        mock_llm_instance = MagicMock()
        mock_get_llm.return_value = mock_llm_instance
        yield mock_llm_instance

def test_1_successful_generation(mock_llm_factory):
    """Test 1: Graph successfully processes valid Python code and generates tests."""
    mock_llm_factory.invoke.side_effect = [
        "# Mocked Test Plan",
        "def test_mock():\n    assert True"
    ]
    
    graph = TestsGeneratorGraph()
    valid_code = "def add(a, b):\n    return a + b"
    
    result = graph.run(source_code=valid_code)
    
    assert result["error"] is None
    assert result["test_plan"] == "# Mocked Test Plan"
    assert result["generated_tests"] == "def test_mock():\n    assert True"
    assert mock_llm_factory.invoke.call_count == 2

def test_2_syntax_error_handling(mock_llm_factory):
    """Test 2: Graph gracefully handles invalid Python code and halts execution."""
    graph = TestsGeneratorGraph()
    invalid_code = "def add(a, b) return a + b" 
    
    result = graph.run(source_code=invalid_code)
    
    assert result["error"] is not None
    assert result["test_plan"] is None
    assert result["generated_tests"] is None
    mock_llm_factory.invoke.assert_not_called()

@patch('use_cases.tests_generator.src.main.generator_agent.run')
def test_3_endpoint_success(mock_graph_run):
    """Test 3: Verifies the FastAPI endpoint returns the expected JSON structure on success."""
    mock_graph_run.return_value = {
        "error": None,
        "test_plan": "# API Test Plan",
        "generated_tests": "def test_api():\n    pass"
    }
    
    response = client.post("/generate-tests", json={
        "source_code": "def sub(a, b):\n    return a - b",
        "module_name": "math_ops"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["module_tested"] == "math_ops"
    assert data["test_plan"] == "# API Test Plan"
    assert data["generated_code"] == "def test_api():\n    pass"

def test_4_endpoint_invalid_payload():
    """Test 4: Verifies the FastAPI endpoint rejects requests missing required fields."""
    response = client.post("/generate-tests", json={
        "source_code": "def sub(a, b):\n    return a - b"
    })
    
    assert response.status_code == 422