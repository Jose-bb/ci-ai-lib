import os
import asyncio
from dotenv import load_dotenv

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langgraph.graph import StateGraph, MessagesState, START, END

from fastmcp import Client
from fastmcp.client.elicitation import ElicitResult, ElicitRequestParams, RequestContext

# Load environment variables
load_dotenv()

async def my_elicitation_handler(message: str, response_type: type | None, params: ElicitRequestParams, context: RequestContext) -> ElicitResult:
    """Handler triggered when the FastMCP server pauses execution for human input."""
    print("\n" + "="*70)
    print("HUMAN-IN-THE-LOOP: AUTHORIZATION REQUIRED")
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
    # Initialize Azure wrapper
    llm = AzureChatOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_deployment=os.getenv("AZURE_OPENAI_MODEL"),
        model=os.getenv("AZURE_OPENAI_MODEL"),
        temperature=0
    )

    # Initialize the FastMCP Client
    server_script_path = "use_cases/user_elicitation/src/server.py"
    mcp_client = Client(
        server_script_path,
        elicitation_handler=my_elicitation_handler
    )

    # Run the graph inside the MCP async context to keep the connection alive
    async with mcp_client:
        
        # Extract tools and format them for LangChain/OpenAI
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
        
        # Bind the raw OpenAI schemas to the LangChain LLM
        llm_with_tools = llm.bind_tools(openai_tools)

        # Define Graph Nodes
        async def agent_node(state: MessagesState):
            """Calls the LLM to decide the next action."""
            response = await llm_with_tools.ainvoke(state["messages"])
            return {"messages": [response]}

        async def action_node(state: MessagesState):
            """Executes the tool via FastMCP and returns the result."""
            last_message = state["messages"][-1]
            results = []
            
            for tool_call in last_message.tool_calls:
                function_name = tool_call["name"]
                function_args = tool_call["args"]
                
                print(f"\nLangGraph routing to action: '{function_name}'...")
                
                try:
                    # Execute the tool via MCP (Triggers the elicitation pause)
                    tool_result = await mcp_client.call_tool(
                        function_name,
                        arguments=function_args
                    )
                    
                    # Safely extract the result string
                    result_content = getattr(tool_result, 'content', [])
                    if isinstance(result_content, list) and len(result_content) > 0:
                        result_text = getattr(result_content[0], 'text', str(result_content[0]))
                    else:
                        result_text = str(getattr(tool_result, 'data', tool_result))
                        
                    print("Tool execution completed. Result returned to LangGraph.")
                    
                    # LangChain requires a ToolMessage to represent the result
                    results.append(ToolMessage(
                        content=str(result_text),
                        name=function_name,
                        tool_call_id=tool_call["id"]
                    ))
                    
                except Exception as e:
                    print(f"Error during tool execution: {e}")
                    results.append(ToolMessage(
                        content=f"Error executing tool: {str(e)}",
                        name=function_name,
                        tool_call_id=tool_call["id"]
                    ))
                    
            return {"messages": results}

        # Define Graph Routing
        def should_continue(state: MessagesState) -> str:
            """Determines if the graph should execute a tool or finish."""
            last_message = state["messages"][-1]
            if last_message.tool_calls:
                return "action"
            return END

        # Build and Compile the StateGraph
        workflow = StateGraph(MessagesState)
        
        workflow.add_node("agent", agent_node)
        workflow.add_node("action", action_node)
        
        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges("agent", should_continue, ["action", END])
        workflow.add_edge("action", "agent")
        
        app = workflow.compile()
        
        system_prompt = SystemMessage(content=(
            "You are a strictly specialized DevOps AI agent running on the user's local machine. "
            "Your ONLY purpose is to manage system health, list available models, and deploy models. "
            "CRITICAL INSTRUCTIONS:\n"
            "1. If the user asks ANY question unrelated to CI/CD, DevOps, system metrics, or deployments (e.g., recipes, sports, general knowledge, coding help outside DevOps), you MUST politely refuse to answer and remind them of your specific purpose.\n"
            "2. When you need to use tools, call them immediately without asking for permission in the chat. "
            "The deployment tool itself has built-in security that will handle the human authorization."
        ))

        print("\n" + "="*50)
        print("CI/CD DEV-OPS AGENT STARTED")
        print("Type 'exit' or 'quit' to close the terminal.")
        print("="*50 + "\n")

        # Initialise the state with the system prompt
        conversation_state = {"messages": [system_prompt]}

        while True:
            try:
                # Ask the user for input
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['exit', 'quit']:
                    print("Shutting down agent...")
                    break
                    
                if not user_input:
                    continue

                # Add the user's message to memory
                conversation_state["messages"].append(HumanMessage(content=user_input))
                
                print("Agent is thinking...")

                # Call the graph. LangGraph keeps a complete record of the conversation.
                conversation_state = await app.ainvoke(conversation_state)
                
                # Print the agent's final response
                final_ai_message = conversation_state['messages'][-1].content
                print(f"\nAgent: {final_ai_message}\n")

            except KeyboardInterrupt:
                print("\nShutting down agent (Interrupted)...")
                break
            except Exception as e:
                print(f"\nAn error occurred: {e}")
                break

if __name__ == "__main__":
    asyncio.run(main())