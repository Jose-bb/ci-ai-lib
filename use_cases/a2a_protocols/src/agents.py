import os
import autogen

# Calculate the absolute path to the workspace folder within the use case
current_dir = os.path.dirname(os.path.abspath(__file__))
workspace_dir = os.path.join(current_dir, "..", "workspace")

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