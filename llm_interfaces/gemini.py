# import os
# import google.generativeai as genai
# from typing import Generator, List, Dict, Optional
# from llm_interfaces.base import LLMInterface

# class GeminiAdapter(LLMInterface):
#     '''
#     GeminiAdapter class is a wrapper class for Google Gemini API. It provides methods to interact with Google Gemini API.
#     '''
#     def __init__(self, api_key: str):
#         '''
#         Initialize the GeminiAdapter class with the Google Gemini API.

#         Args:
#             api_key (str): The Google Gemini API key.
#         '''
#         genai.configure(api_key=api_key)

#     def _convert_messages(self, messages: List[Dict[str, str]]) -> List[Dict]:
#         '''
#         Convert messages from OpenAI format to Gemini format.

#         Args:
#             messages (list[dict]): A list of dictionaries containing the messages to be processed.

#         Returns:
#             list[dict]: The converted messages for Gemini.
#         '''
#         gemini_messages = []
#         for msg in messages:
#             role = "user" if msg["role"] == "user" else "model"
#             gemini_messages.append({"role": role, "parts": [msg["content"]]})
#         return gemini_messages

#     def invoke(self, messages: List[Dict[str, str]], model: str, tools: Optional[List[Dict]] = None) -> str:
#         '''
#         Invoke the LLM model with the previously formatted messages.

#         Args:
#             messages (list[dict]): A list of dictionaries containing the messages to be processed.
#             model (str): The LLM model to be used.
#             tools (list[dict], optional): The list of tools to be used by the model.

#         Returns:
#             str: The response from the LLM model.
#         '''
#         model_instance = genai.GenerativeModel(model)
#         gemini_history = self._convert_messages(messages[:-1])
#         user_msg = messages[-1]["content"]
        
#         chat = model_instance.start_chat(history=gemini_history)
#         response = chat.send_message(user_msg)
#         return response.text

#     def invoke_stream(self, messages: List[Dict[str, str]], model: str) -> Generator[str, None, None]:
#         '''
#         Invoke the LLM model with the previously formatted messages using the stream API.

#         Args:
#             messages (list[dict]): A list of dictionaries containing the messages to be processed.
#             model (str): The LLM model to be used.

#         Returns:
#             Generator: The response chunks from the LLM model.
#         '''
#         model_instance = genai.GenerativeModel(model)
#         gemini_history = self._convert_messages(messages[:-1])
#         user_msg = messages[-1]["content"]
        
#         chat = model_instance.start_chat(history=gemini_history)
#         response = chat.send_message(user_msg, stream=True)
#         for chunk in response:
#             yield chunk.text
