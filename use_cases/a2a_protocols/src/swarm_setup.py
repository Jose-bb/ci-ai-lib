import os
import autogen
from dotenv import load_dotenv

# Import the predefined agents from our agents module and tools
from use_cases.a2a_protocols.src.agents import (user_proxy, software_agent, hardware_agent, architect_agent)

# Tools
from use_cases.a2a_protocols.src.tools.gpu_metrics import get_vram_status
from use_cases.a2a_protocols.src.tools.docker_logs import get_docker_logs
from use_cases.a2a_protocols.src.tools.system_health import get_system_ram_cpu

def setup_swarm():
    """Instantiates the AutoGen GroupChat and its routing Manager."""
    load_dotenv()

    # AutoGen requires a specific dictionary format for model configuration
    llm_config = {
        "config_list": [
            {
                "model": os.getenv("AZURE_OPENAI_MODEL"),
                "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
                "base_url": os.getenv("AZURE_OPENAI_ENDPOINT"),
                "api_type": "azure",
                "api_version": os.getenv("AZURE_OPENAI_API_VERSION"),
                "default_headers": {
                    "Authorization": f"Bearer {os.getenv('AZURE_OPENAI_API_KEY')}",
                    "api-key": os.getenv("AZURE_OPENAI_API_KEY")
                }
            }
        ],
        "temperature": 0.2, # Kept low for deterministic and highly technical answers
    }

    software_agent.llm_config = llm_config.copy()
    hardware_agent.llm_config = llm_config.copy()
    architect_agent.llm_config = llm_config.copy()

    # Bind the OpenAI client to the expert agents dynamically
    software_agent.client = autogen.OpenAIWrapper(**llm_config)
    hardware_agent.client = autogen.OpenAIWrapper(**llm_config)
    architect_agent.client = autogen.OpenAIWrapper(**llm_config)

    # Tool registration: Define the list of tools and who owns them
    tool_registry = [
        {
            "func": get_vram_status,
            "caller": hardware_agent,
            "desc": "Checks the current GPU VRAM allocation."
        },
        {
            "func": get_system_ram_cpu,
            "caller": hardware_agent,
            "desc": "Checks the host machine's CPU and RAM."
        },
        {
            "func": get_docker_logs,
            "caller": software_agent,
            "desc": "Fetches logs from a specified Docker container."
        }
    ]

    # Iterate and register dynamically
    for tool in tool_registry:
        autogen.agentchat.register_function(
            tool["func"],
            caller=tool["caller"],
            executor=user_proxy,
            name=tool["func"].__name__,
            description=tool["desc"],
        )

    # Swarm (Group Chat) Instantiation
    committee_chat = autogen.GroupChat(
        agents=[user_proxy, software_agent, hardware_agent, architect_agent],
        messages=[],
        max_round=15, # Hard limit failsafe to prevent infinite API billing loops
        speaker_selection_method="auto", 
        allow_repeat_speaker=False, # Forces cross-communication, preventing an agent from talking to itself
    )

    # Chat Manager Setup
    swarm_manager = autogen.GroupChatManager(
        groupchat=committee_chat,
        llm_config=llm_config,
    )

    return user_proxy, swarm_manager