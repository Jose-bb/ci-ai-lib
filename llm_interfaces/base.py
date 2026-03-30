from abc import ABC, abstractmethod
from typing import Generator, List, Dict, Optional

class LLMInterface(ABC):
    '''
    Abstract interface for all LLM implementations.
    '''
    @abstractmethod
    def invoke(self, messages: List[Dict[str, str]], model: str, tools: Optional[List[Dict]] = None) -> str:
        '''
        Send a list of messages to the LLM and return the assistant's response.

        Args:
            messages (List[Dict[str, str]]): A list of dictionaries containing the messages to be processed.
            model (str): The LLM model to be used.
            tools (List[Dict], optional): The list of tools to be used by the model.

        Returns:
            str: The response from the LLM model.
        '''
        pass

    @abstractmethod
    def invoke_stream(self, messages: List[Dict[str, str]], model: str) -> Generator[str, None, None]:
        '''
        Send a list of messages to the LLM and yield chunks of the assistant's response.

        Args:
            messages (List[Dict[str, str]]): A list of dictionaries containing the messages to be processed.
            model (str): The LLM model to be used.

        Returns:
            Generator[str, None, None]: The response chunks from the LLM model.
        '''
        pass
