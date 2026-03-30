import os
import json
from typing import Generator, List, Dict, Optional
from openai import AzureOpenAI
from llm_interfaces.base import LLMInterface

class AzureOpenAIAdapter(LLMInterface):
    '''
    AzureOpenAI class is a wrapper class for Azure OpenAI API. It provides methods to interact with Azure OpenAI API.
    '''
    def __init__(self, api_key: str, api_version: str, azure_endpoint: str):
        '''
        Initialize the AzureOpenAI class with the Azure OpenAI API.

        Args:
            api_key (str): The Azure OpenAI API key.
            api_version (str): The Azure OpenAI API version.
            azure_endpoint (str): The Azure OpenAI endpoint.
        '''
        self.client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=azure_endpoint
        )

    def invoke(self, messages: List[Dict[str, str]], model: str, tools: Optional[List[Dict]] = None) -> str:
        '''
        Invoke the LLM model with the previously formatted messages.

        Args:
            messages (list[dict]): A list of dictionaries containing the messages to be processed.
            model (str): The LLM model to be used.
            tools (list[dict], optional): The list of tools to be used by the model.

        Returns:
            str: The response from the LLM model.
        '''
        params = {
            "model": model,
            "messages": messages
        }
        if tools:
            params["tools"] = tools

        response = self.client.chat.completions.create(**params)
        return response.choices[0].message.content

    def invoke_stream(self, messages: List[Dict[str, str]], model: str) -> Generator[str, None, None]:
        '''
        Invoke the LLM model with the previously formatted messages using the stream API.

        Args:
            messages (list[dict]): A list of dictionaries containing the messages to be processed.
            model (str): The LLM model to be used.

        Returns:
            Generator: The response from the LLM model.
        '''
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True
        )

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
