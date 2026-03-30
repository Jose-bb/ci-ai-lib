import pytest
import os
import sys
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

# Ensure the root directory and src directory are in sys.path
# Now it's 3 levels up: test -> simple_llm_call -> use_cases -> root
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.append(root_path)

from use_cases.simple_llm_call.src.main import app

client = TestClient(app)

def test_health_check():
    '''
    Test the health check endpoint.
    '''
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@patch("use_cases.simple_llm_call.src.main.LLMFactory.get_llm")
def test_chat_endpoint(mock_get_llm):
    '''
    Test the chat endpoint.
    '''
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = "Mocked Response"
    mock_get_llm.return_value = mock_llm

    payload = {
        "messages": [{"role": "user", "content": "hi"}],
        "model": "gpt-4",
        "provider": "azure_openai"
    }
    
    response = client.post("/chat", json=payload)
    
    assert response.status_code == 200
    assert response.json() == {"response": "Mocked Response"}
    
    mock_get_llm.assert_called_once_with(provider="azure_openai")
    mock_llm.invoke.assert_called_once()
