import json
from typing import Generator

from openai import AzureOpenAI

from src.utils.config import config
from src.agents.base_agent import BaseAgent
from src.tools.tool_executor import call_function

formatter = None


class AzureOpenAIAdapter(BaseAgent):
    '''
    AzureOpenAI class is a wrapper class for Azure OpenAI API. It provides methods to interact with Azure OpenAI API.
    '''
    def __init__(self):
        '''
        Initialize the AzureOpenAI class with the Azure OpenAI API.
        '''
        self.client = AzureOpenAI(
            api_key=config.get('OPENAI_API_KEY'),
            api_version=config.get('OPENAI_API_VERSION'),
            azure_endpoint=config.get('OPENAI_API_BASE')
        )


    def invoke_llm(self, messages: list[dict], model: str, tools: list[dict]=None) -> str:
        '''
        Invoke the LLM model with the previously formatted messages.

        Args:
            messages (list[dict]): A list of dictionaries containing the messages to be processed.
            model (str): The LLM model to be used.
            tools (list[dict], optional): The list of tools to be used by the agent.

        Returns:
            str: The response from the LLM model.
        '''
        if tools:
            messages = self.call_tools(messages, model, tools)

        response = self.client.chat.completions.create(
            model=model,
            messages=messages
        )

        return response.choices[0].message.content


    def invoke_llm_stream(self, messages: list[dict], model: str, tools: list[dict]=None) -> Generator:
        '''
        Invoke the LLM model with the previously formatted messages using the stream API.

        Args:
            messages (list[dict]): A list of dictionaries containing the messages to be processed.
            model (str): The LLM model to be used.
            tools (list[dict], optional): The list of tools to be used by the agent.

        Returns:
            str: The response from the LLM model.
        '''
        if tools:
            messages = self.call_tools(messages, model, tools)
        
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True
        )

        for chunk in response:
            if chunk.choices:
                yield chunk.choices[0].delta.content


    def invoke_llm_format(self, users_query: str, instructions: str, model: str) -> str:
        '''
        Format the messages to be sent to the LLM model.

        Args:
            users_query (str): The users requests.
            instructions (str): The prompt with the models instructions.
            model (str): The LLM model to be used.

        Returns:
            str: The name of the next agent to be called.
        '''
        global formatter
        if not formatter:
            from src.agents.agent_validator import CallAgentFormatter
            formatter = CallAgentFormatter

        messages = self.compose_messages(
            users_query=users_query,
            instructions=instructions
        )
        
        response = self.client.chat.completions.parse(
            model=model,
            messages=messages,
            response_format=CallAgentFormatter
        )

        next_agent = response.choices[0].message.parsed.next_agent

        return next_agent


    def call_tools(self, messages: list[dict], model: str, tools: dict) -> str:
        '''
        Use the tool calling methods of the LLM model to process the messages.

        Args:
            messages (list[dict]): A list of dictionaries containing the messages to be processed.
            model (str): The LLM model to be used.
            tools (dict): Dictionary with the tools available for the agent.

        Returns:
            str: The tool response from the LLM model.
        '''
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools
        )

        messages.append(response.choices[0].message)

        for tool_call in response.choices[0].message.tool_calls or []:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            result = call_function(name, args)

            messages.append({
                'role': 'tool',
                'tool_call_id': tool_call.id,
                'content': str(result),
            })

        return messages


    def compose_messages(self, users_query: str, instructions: str) -> list[dict]:
        '''
        Compose the messages with the users query and model instructions.

        Args:
            users_query (str): The users requests.
            instructions (str): The prompt with the models instructions.

        Returns:
            list[dict]: The composed messages for the model.
        '''
        return [
            {'role': 'system', 'content': instructions},
            {'role': 'user', 'content': users_query}
        ]
    

    def call_agent(self, agents: list[dict], users_query: str, model: str) -> dict:
        '''
        Calls another agent to process the users query.

        Args:
            agents (list[dict]): The list of agents to be used by the agent.
            users_query (str): Users query to be answered.
            model (str): The LLM model to be used.

        Returns:
            dict: The LLM's response to the users petition.
        '''
        available_agents = {agent['name']: agent['description'] for agent in agents}

        next_agent = self.invoke_llm_format(
            users_query=users_query,
            instructions=f'Based on the available agents, decide which agent is best suited to answer the user query. Respond with the name of the agent only. Available agents: {json.dumps(available_agents)}.',
            model=model
        )

        if not next_agent:
            return 'No suitable agent found to handle the request.'
        
        selected_agent = next((agent for agent in agents if agent['name'] == next_agent), None)
        if not selected_agent:
            return 'The selected agent does not exist.'
        
        agent_llm = selected_agent['llm']
        messages = agent_llm.compose_messages(
            users_query=users_query,
            instructions=selected_agent['prompt']
        )
        tools = selected_agent.get('tools', None)
        
        return {'role': 'assistant', 'content': agent_llm.invoke_llm(messages, model, tools)}