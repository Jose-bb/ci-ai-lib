import asyncio

from fastmcp import Client
from fastmcp.client.elicitation import ElicitResult, ElicitRequestParams, RequestContext

async def my_elicitation_handler(message: str, response_type: type | None, params: ElicitRequestParams, context: RequestContext) -> ElicitResult:
    """Handler triggered when the server pauses execution to request human input."""
    print("\n" + "="*60)
    print("ELICITATION REQUEST FROM SERVER")
    print("="*60)
    print(f"Message: {message}\n")
    
    # Capture user input via terminal
    user_decision = input("Do you confirm the action? (yes/no): ").strip().lower()
    reason = input("Please provide a reason (optional): ").strip()
    
    print("="*60 + "\n")

    # Process the decision and return the ElicitResult
    if user_decision in ['yes', 'y', 'no', 'n']:
        is_confirmed = user_decision in ['yes', 'y']
        
        # We pack the data into the auto-generated response_type class
        if response_type:
            response_data = response_type(is_confirmed=is_confirmed, reason=reason)
            return ElicitResult(action="accept", content=response_data)
        
        return ElicitResult(action="accept")
        
    else:
        # If the user types something invalid, we cancel the operation
        print("Invalid input detected. Cancelling operation...")
        return ElicitResult(action="cancel")


async def main():
    """Main client execution flow."""
    server_script_path = "use_cases/user_elicitation/src/server.py"
    
    client = Client(
        server_script_path,
        elicitation_handler=my_elicitation_handler
    )
    
    # Connect to the server using an async context manager
    async with client:
        print("Client successfully connected to the FastMCP Server.")
        print("Calling tool: 'restart_cluster'...")
        
        try:
            # Call the tool. This will trigger the elicitation handler mid-execution
            result = await client.call_tool(
                "restart_cluster", 
                arguments={"cluster_name": "production-db-01"}
            )
            
            print(f"\nTool execution completed successfully.")
            print(f"Server Response: {getattr(result, 'data', result)}")
            
        except Exception as e:
            print(f"\nError during tool execution: {e}")

if __name__ == "__main__":
    asyncio.run(main())