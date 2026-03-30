import pytest
from unittest.mock import MagicMock, patch
from llm_interfaces.azure_openai import AzureOpenAIAdapter
from llm_interfaces.gemini import GeminiAdapter
from llm_interfaces.factory import LLMFactory

def test_azure_openai_adapter_invoke():
    '''
    Test the invoke method of AzureOpenAIAdapter.
    '''
    with patch('llm_interfaces.azure_openai.AzureOpenAI') as mock_openai:
        mock_client = mock_openai.return_value
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Hello world"))]
        mock_client.chat.completions.create.return_value = mock_response

        adapter = AzureOpenAIAdapter(api_key="test", api_version="test", azure_endpoint="test")
        messages = [{"role": "user", "content": "hi"}]
        response = adapter.invoke(messages, "gpt-4")

        assert response == "Hello world"
        mock_client.chat.completions.create.assert_called_once()

def test_gemini_adapter_invoke():
    '''
    Test the invoke method of GeminiAdapter.
    '''
    with patch('google.generativeai.GenerativeModel') as mock_model, \
         patch('google.generativeai.configure') as mock_config:
        
        mock_instance = mock_model.return_value
        mock_chat = mock_instance.start_chat.return_value
        mock_response = MagicMock()
        mock_response.text = "Hello Gemini"
        mock_chat.send_message.return_value = mock_response

        adapter = GeminiAdapter(api_key="test")
        messages = [{"role": "user", "content": "hi"}]
        response = adapter.invoke(messages, "gemini-pro")

        assert response == "Hello Gemini"
        mock_chat.send_message.assert_called_once_with("hi")

def test_llm_factory_get_llm():
    '''
    Test the LLMFactory to ensure it returns the correct adapter.
    '''
    with patch.dict('os.environ', {
        "AZURE_OPENAI_API_KEY": "test",
        "AZURE_OPENAI_ENDPOINT": "test",
        "GEMINI_API_KEY": "test"
    }):
        azure_llm = LLMFactory.get_llm(provider="azure_openai")
        assert isinstance(azure_llm, AzureOpenAIAdapter)

        gemini_llm = LLMFactory.get_llm(provider="gemini")
        assert isinstance(gemini_llm, GeminiAdapter)
