import os
import json
import asyncio
from dotenv import load_dotenv

from openai import AsyncAzureOpenAI
from fastmcp import Client
from fastmcp.client.elicitation import ElicitResult, ElicitRequestParams, RequestContext

load_dotenv()

async def my_elicitation_handler(message: str, response_type: type | None, params: ElicitRequestParams, context: RequestContext) -> ElicitResult:
    """Handler triggered when the server pauses execution for human input."""
    print("\n" + "="*70)
    print("HUMAN-IN-THE-LOOP: AUTHORIZATION REQUIRED BY AGENT")
    print("="*70)
    print(f"Message: {message}\n")
    
    user_decision = input("Do you confirm the deployment? (yes/no): ").strip().lower()
    reason = input("Please provide a reason (optional): ").strip()
    
    print("="*70 + "\n")

    if user_decision in ['yes', 'y', 'no', 'n']:
        is_confirmed = user_decision in ['yes', 'y']
        
        if response_type:
            response_data = response_type(is_confirmed=is_confirmed, reason=reason)
            return ElicitResult(action="accept", content=response_data)
        
        return ElicitResult(action="accept")
    else:
        print("Invalid input detected. Cancelling operation...")
        return ElicitResult(action="cancel")


async def main():
    # Initialize the Azure OpenAI Client
    llm = AsyncAzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )
    deployment_name = os.getenv("AZURE_OPENAI_MODEL")

    # Initialize the FastMCP Client
    server_script_path = "use_cases/user_elicitation/src/server.py"
    mcp_client = Client(
        server_script_path,
        elicitation_handler=my_elicitation_handler
    )

    async with mcp_client:
        print("MCP Client connected to the Server.")
        
        # Extract tools from the MCP server and format them for OpenAI
        tools_response = await mcp_client.list_tools()
        mcp_tools = getattr(tools_response, 'tools', tools_response)
        
        openai_tools = []
        for tool in mcp_tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            })
        
        print(f"Agent loaded with tools: {[t['function']['name'] for t in openai_tools]}")

        # Define the initial conversation
        # 4. Define the initial conversation
        messages = [
            {
                "role": "system", 
                "content": (
                    "You are a DevOps AI agent managing ML model deployments. "
                    "CRITICAL INSTRUCTION: When the user asks for a deployment, you MUST call the deployment tool IMMEDIATELY. "
                    "DO NOT ask the user for permission or confirmation in the chat. The tool itself has built-in security "
                    "that will handle the human authorization. Just call the tool, wait for the result, and then summarize the final outcome."
                )
            },
            {
                "role": "user", 
                "content": "Please deploy the new audio-to-text whisper model to the production environment."
            }
        ]
        
        print("\nUser: Please deploy the new audio-to-text whisper model to the production environment.")
        print("Agent is thinking and evaluating tools...\n")

        # Call Azure OpenAI to decide the next action
        response = await llm.chat.completions.create(
            model=deployment_name,
            messages=messages,
            tools=openai_tools,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        
        # Check if the LLM decided to call our tool
        if response_message.tool_calls:
            # Append the assistant's decision to the conversation history
            messages.append(response_message) 
            
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                print(f"Agent decided to call '{function_name}' with args: {function_args}")
                
                try:
                    # Execute the tool via MCP (This pauses execution and triggers the elicitation handler!)
                    tool_result = await mcp_client.call_tool(
                        function_name,
                        arguments=function_args
                    )
                    
                    # Safely extract the result string from the MCP standard format
                    result_content = getattr(tool_result, 'content', [])
                    if isinstance(result_content, list) and len(result_content) > 0:
                        result_text = getattr(result_content[0], 'text', str(result_content[0]))
                    else:
                        result_text = str(getattr(tool_result, 'data', tool_result))
                        
                    print(f"Tool execution completed. Result payload received from server.")
                    
                    # Append the tool execution result back to the conversation
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": str(result_text)
                    })
                    
                except Exception as e:
                    print(f"\nError during tool execution: {e}")
                    return
                    
            # Final LLM generation summarizing the Human-in-the-Loop outcome
            print("\nAgent is summarizing the final outcome...")
            final_response = await llm.chat.completions.create(
                model=deployment_name,
                messages=messages
            )
            print(f"\nFinal Agent Response:\n{final_response.choices[0].message.content}\n")

        else:
            print(f"Agent answered without using tools: {response_message.content}")

if __name__ == "__main__":
    asyncio.run(main())