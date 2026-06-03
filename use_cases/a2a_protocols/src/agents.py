import autogen

# Human Avatar (User Elicitation): Represents the user in the chat. Triggers terminal prompts for context
user_proxy = autogen.UserProxyAgent(
    name="User_Proxy",
    system_message=(
        "A human admin. I can provide additional context, approve tools, or clarify errors. "
        "Route the conversation to me if you need human input."
    ),
    human_input_mode="TERMINATE", 
    is_termination_msg=lambda msg: "TERMINATE" in msg.get("content", ""),
    code_execution_config={
        "work_dir": "workspace", 
        "use_docker": False
    }, 
)

# Software Engineering Agent: Code optimization, AI frameworks, and scripting.
software_agent = autogen.AssistantAgent(
    name="Software_Engineer",
    system_message=(
        "You are a Senior Software Engineer specializing in Python, AI deployment, "
        "and memory optimization. Your primary goal is to analyze scripts and error logs "
        "to identify inefficiencies, memory leaks, or logical bugs. "
        "CRITICAL: If the error log is incomplete or you need more context about the "
        "deployment environment, directly ask the 'User_Proxy' for clarification. "
        "IMPORTANT: If you ask the User_Proxy a question, you MUST append the exact word "
        "'TERMINATE' at the end of your message. This acts as a pause signal so the human can reply. "
        "You must actively consult the 'Hardware_Specialist' if you suspect physical constraints. "
        "Always propose concrete code snippets to solve the issue."
    ),
    llm_config=False,  # The configuration is injected dynamically in swarm_setup.py
)

# Hardware & Infrastructure Agent: System resources, VRAM, CPU limits, and physical bottlenecks.
hardware_agent = autogen.AssistantAgent(
    name="Hardware_Specialist",
    system_message=(
        "You are a Senior Infrastructure and Hardware Specialist. "
        "Your expertise lies in diagnosing system bottlenecks, GPU VRAM saturation, "
        "and memory allocation limits. "
        "When evaluating solutions, if you lack information about the physical machine "
        "(e.g., total VRAM, OS, CPU architecture), ask the 'User_Proxy' before making assumptions. "
        "IMPORTANT: If you ask the User_Proxy a question, you MUST append the exact word "
        "'TERMINATE' at the end of your message. This acts as a pause signal so the human can reply. "
        "Provide hard limits and technical specifications."
    ),
    llm_config=False,
)

# Lead Architect Agent: Decision maker, moderator, and final reviewer.
architect_agent = autogen.AssistantAgent(
    name="Chief_Architect",
    system_message=(
        "You are the Chief System Architect leading this troubleshooting committee. "
        "You evaluate the debate between the Software_Engineer and the Hardware_Specialist. "
        "If you feel the proposed solution does not align with business rules, ask the 'User_Proxy' "
        "for strategic validation (remembering to append 'TERMINATE' to let them answer). "
        "Once a stable, cross-validated solution is reached, summarize the final "
        "architectural decision and append the exact word 'TERMINATE' to end the session."
    ),
    llm_config=False,
)