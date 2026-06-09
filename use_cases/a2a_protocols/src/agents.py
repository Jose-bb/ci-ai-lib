import os
import autogen
import asyncio

from use_cases.a2a_protocols.utilities.cost_tracker import calculate_turn_cost, format_telemetry_cost

# Calculate the absolute path to the workspace folder within the use case
current_dir = os.path.dirname(os.path.abspath(__file__))
workspace_dir = os.path.join(current_dir, "..", "workspace")

# Custom Proxy to bridge AutoGen's human input with FastAPI WebSockets
class WebSocketUserProxyAgent(autogen.UserProxyAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Create an async lock to prevent concurrency collisions on the WebSocket
        self.ws_lock = asyncio.Lock()

    async def a_get_human_input(self, prompt: str) -> str:
        """Overrides the native async input to route through the WebSocket with a concurrency lock."""
        if hasattr(self, "websocket") and self.websocket:
            # The lock ensures only one tool can ask the human for input at a time
            async with self.ws_lock:
                try:
                    # Send the authorization/input request to the frontend
                    await self.websocket.send_json({
                        "type": "human_input_request",
                        "prompt": prompt
                    })
                    # Pause execution and wait for the human's response via the socket
                    data = await self.websocket.receive_json()
                    # Extract the answer (e.g., "y", "n", or extra context)
                    return data.get("content", "")
                except Exception as e:
                    print(f"WebSocket input error: {e}")
                    # If the socket fails, wait 1s to prevent cpu-burning infinite loops
                    await asyncio.sleep(1)
                    return ""
        else:
            # Fallback: if no websocket is attached, use the standard console
            return await super().a_get_human_input(prompt)

# Human Avatar (User Elicitation): Represents the user in the chat. Triggers terminal prompts for context
user_proxy = WebSocketUserProxyAgent(
    name="User_Proxy",
    system_message=(
        "A human admin. I can provide additional context, approve tools, or clarify errors. "
        "Route the conversation to me if you need human input."
    ),
    human_input_mode="TERMINATE", 
    is_termination_msg=lambda msg: "TERMINATE" in msg.get("content", ""),
    code_execution_config={
        "work_dir": workspace_dir,
        "use_docker": False
    }, 
)

# Software Engineering Agent: Code optimization, AI frameworks, and scripting
software_agent = autogen.AssistantAgent(
    name="Software_Engineer",
    system_message=(
        "You are a Senior Software Engineer specializing in Python, AI deployment, and memory optimization. "
        "Your primary goal is to analyze scripts and error logs to identify inefficiencies, memory leaks, or logical bugs. "
        "CRITICAL: If the error log is incomplete or you need more context about the deployment environment, "
        "directly ask the 'User_Proxy' for clarification. "
        "IMPORTANT: If you ask the User_Proxy a question, you MUST append the exact word 'TERMINATE' "
        "at the end of your message. This acts as a pause signal so the human can reply. "
        "PROACTIVE TOOL USE & DELEGATION: You are equipped with software-level diagnostic tools (e.g., reading logs or code). "
        "Proactively use your tools to investigate errors BEFORE making assumptions. "
        "If a metric is out of your domain (like physical hardware limits), DO NOT ask the 'User_Proxy' to run manual commands. "
        "Instead, ask your team members (like the 'Hardware_Specialist') to use their specialized tools."
        "Always propose concrete code snippets to solve the issue. "
        "CODE EXECUTION RULE: If you provide a code block that is just an EXAMPLE and not meant to be "
        "automatically executed by the system, wrap it in ```text instead of ```python."
    ),
    llm_config=False,  # The configuration is injected dynamically in swarm_setup.py
)

# Hardware & Infrastructure Agent: System resources, VRAM, CPU limits, and physical bottlenecks
hardware_agent = autogen.AssistantAgent(
    name="Hardware_Specialist",
    system_message=(
        "You are a Senior Infrastructure and Hardware Specialist. "
        "Your expertise lies in diagnosing system bottlenecks, GPU VRAM saturation, and memory allocation limits. "
        "PROACTIVE TOOL USE: You are equipped with automated diagnostic tools. If a problem falls within your domain "
        "(e.g., hardware metrics, VRAM), proactively execute your registered tools to gather real data BEFORE "
        "making assumptions or asking the human for manual metrics. "
        "When evaluating solutions, if you still lack information about the physical machine after using your tools, "
        "ask the 'User_Proxy' for clarification. "
        "IMPORTANT: If you ask the User_Proxy a question, you MUST append the exact word 'TERMINATE' "
        "at the end of your message. Provide hard limits and technical specifications."
    ),
    llm_config=False,
)

# Lead Architect Agent: Decision maker, moderator, and the only client-facing agent.
architect_agent = autogen.AssistantAgent(
    name="Chief_Architect",
    system_message=(
        "You are the Lead System Architect and the ONLY agent allowed to present final summaries or ask questions to the human user. "
        "Your job is to translate the technical debate between the Software_Engineer and Hardware_Specialist into clear, actionable, and human-friendly advice. "
        "NEVER use vague corporate jargon like 'strategic validation' or 'business rules'. "
        "If the team needs human input, ask a direct, simple, and specific question (e.g., 'Do you prefer to reduce the batch size or use CPU?', 'What is your current Docker memory limit?'). "
        "Once you present the summary or ask your direct question, append the exact word 'TERMINATE' to end your turn."
    ),
    llm_config=False,
)


# Telemetry Hooks
def telemetry_hook(sender, message, recipient, silent):
    """
    Middleware function that intercepts messages before they are sent.
    It extracts the agent's token usage, calculates the cost, and broadcasts it.
    """
    # cVerify the agent has an active LLM client attached
    if hasattr(sender, "client") and sender.client is not None:
        try:
            usage = getattr(sender.client, "actual_usage_summary", {})
            
            if usage:
                # AutoGen's usage dict contains models as keys
                for model_name, stats in usage.items():
                    if isinstance(stats, dict) and "total_tokens" in stats:
                        p_tokens = stats.get("prompt_tokens", 0)
                        c_tokens = stats.get("completion_tokens", 0)
                        t_tokens = stats.get("total_tokens", 0)

                        # Call the custom utility to calculate the real money cost
                        cost_usd = calculate_turn_cost(p_tokens, c_tokens, model_name)
                        telemetry_msg = format_telemetry_cost(sender.name, t_tokens, cost_usd)

                        # Fire-and-forget the WebSocket message
                        if hasattr(user_proxy, "websocket") and user_proxy.websocket:
                            try:
                                asyncio.create_task(
                                    user_proxy.websocket.send_json({
                                        "type": "status",
                                        "content": telemetry_msg
                                    })
                                )
                            except Exception as e:
                                print(f"Telemetry broadcast error: {e}")
                        
                        # Break after finding the first valid model stats
                        break 
        except Exception as e:
            print(f"[Ops Warning] Error in telemetry hook: {e}")

    # Return the unmodified message so the chat continues normally
    return message

# Register the hook to all LLM-powered agents
software_agent.register_hook(hookable_method="process_message_before_send", hook=telemetry_hook)
hardware_agent.register_hook(hookable_method="process_message_before_send", hook=telemetry_hook)
architect_agent.register_hook(hookable_method="process_message_before_send", hook=telemetry_hook)