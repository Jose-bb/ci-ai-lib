import os
from typing import Optional
from llm_interfaces.base import LLMInterface
from llm_interfaces.azure_openai import AzureOpenAIAdapter
from llm_interfaces.gemini import GeminiAdapter

class LLMFactory:
    '''
    LLMFactory class is a factory for creating LLM adapters.
    '''
    @staticmethod
    def get_llm(provider: Optional[str] = None) -> LLMInterface:
        '''
        Returns an instance of an LLM interface based on provider.

        Args:
            provider (str, optional): The LLM provider to be used (e.g., 'azure_openai', 'gemini').

        Returns:
            LLMInterface: An instance of the requested LLM adapter.
        '''
        provider = provider or os.getenv("LLM_PROVIDER", "azure_openai").lower()

        if provider == "azure_openai":
            return AzureOpenAIAdapter(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2023-12-01-preview"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )
        elif provider == "gemini":
            return GeminiAdapter(
                api_key=os.getenv("GEMINI_API_KEY")
            )
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")
