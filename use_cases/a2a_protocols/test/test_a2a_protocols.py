import os
import sys
import pytest
import warnings
from unittest.mock import patch, MagicMock

# Eliminate flaml's harmless warning
warnings.filterwarnings("ignore", category=UserWarning, module="flaml")

# Ensure the root directory is accessible for absolute imports
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from use_cases.a2a_protocols.src.main import main
from use_cases.a2a_protocols.src.swarm_setup import setup_swarm
from use_cases.a2a_protocols.src.agents import (user_proxy, software_agent, hardware_agent, architect_agent)

class TestA2AProtocols:
    """
    Test suite for the A2A Protocols setup.
    We mock the external dependencies to ensure the architecture logic holds together without incurring Azure API costs.
    """

    @patch("use_cases.a2a_protocols.src.main.setup_swarm")
    def test_1_main_initializes_and_starts_chat(self, mock_setup_swarm):
        """Test 1: Validates that main() successfully extracts the proxy and manager, and triggers initiate_chat."""
        mock_proxy = MagicMock()
        mock_manager = MagicMock()
        mock_setup_swarm.return_value = (mock_proxy, mock_manager)

        main()

        mock_setup_swarm.assert_called_once()
        mock_proxy.initiate_chat.assert_called_once()
        
        args, kwargs = mock_proxy.initiate_chat.call_args
        assert args[0] == mock_manager, "Chat must be initiated with the swarm manager."
        assert "message" in kwargs, "An initial incident message must be provided."
        assert "INCIDENT REPORT" in kwargs["message"], "The message should contain the hardcoded incident."
        assert kwargs["summary_method"] == "reflection_with_llm", "Summary method should be reflection_with_llm."

    @patch("use_cases.a2a_protocols.src.main.setup_swarm")
    @patch("use_cases.a2a_protocols.src.main.sys.exit")
    def test_2_main_handles_initialization_error(self, mock_sys_exit, mock_setup_swarm):
        """Test 2: Validates that if setup_swarm fails, the system exits gracefully with status code 1."""
        mock_setup_swarm.side_effect = Exception("Missing Azure API Key")
        
        mock_sys_exit.side_effect = SystemExit

        with pytest.raises(SystemExit):
            main()

        mock_sys_exit.assert_called_once_with(1)

    @patch("use_cases.a2a_protocols.src.swarm_setup.os.getenv")
    def test_3_setup_swarm_configuration(self, mock_getenv):
        """Test 3: Verifies that setup_swarm structures the LLM config and fallback headers correctly."""
        # Mock environment variables to avoid reading the real .env file during CI pipelines
        mock_getenv.side_effect = lambda k, default="": {
            "AZURE_OPENAI_MODEL": "test-model",
            "AZURE_OPENAI_API_KEY": "test-key-1234567890",
            "AZURE_OPENAI_ENDPOINT": "https://test.endpoint.azure.com/",
            "AZURE_OPENAI_API_VERSION": "2024-02-01"
        }.get(k, default)

        proxy, manager = setup_swarm()

        # Validate core objects
        assert proxy.name == "User_Proxy"
        assert manager.name == "chat_manager"
        assert len(manager.groupchat.agents) == 4
        
        # Validate that the security header patch for JWT tokens is present
        llm_config = manager.llm_config
        assert llm_config["config_list"][0]["api_key"] == "test-key-1234567890"
        assert "default_headers" in llm_config["config_list"][0]
        assert "api-key" in llm_config["config_list"][0]["default_headers"]

    def test_4_agent_definitions_and_constraints(self):
        """Test 4: Ensures the agents have the correct boundaries and foundational constraints."""
        # Check explicit naming (critical for AutoGen routing)
        assert software_agent.name == "Software_Engineer"
        assert hardware_agent.name == "Hardware_Specialist"
        assert architect_agent.name == "Chief_Architect"

        # Check core routing directives in system messages
        assert "User_Proxy" in software_agent.system_message
        assert "TERMINATE" in architect_agent.system_message

    def test_5_user_proxy_termination_logic(self):
        """Test 5: Verifies the lambda function correctly identifies the termination keyword to stop the loop."""
        # Simulate a normal message in the middle of a debate
        normal_msg = {"content": "I recommend checking the VRAM parameters in Docker."}
        # Call the internal method AutoGen uses to check for termination
        assert not user_proxy._is_termination_msg(normal_msg)

        # Simulate the architect's final veredict
        term_msg = {"content": "This concludes the session. TERMINATE"}
        assert user_proxy._is_termination_msg(term_msg)