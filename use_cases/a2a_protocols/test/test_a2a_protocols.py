import os
import sys
import pytest
import warnings
import argparse
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
    Test suite for the A2A Protocols setup (V2).
    Validates dynamic CLI inputs, Tool registration, and correct routing without incurring Azure API costs.
    """

    @patch("use_cases.a2a_protocols.src.main.setup_swarm")
    @patch("use_cases.a2a_protocols.src.main.argparse.ArgumentParser.parse_args")
    def test_1_main_initializes_with_cli_args(self, mock_parse_args, mock_setup_swarm):
        """Test 1: Validates that main() reads CLI arguments and initiates the chat properly."""
        # Mock the CLI arguments
        mock_args = argparse.Namespace(incident="Test OOM crash")
        mock_parse_args.return_value = mock_args

        mock_proxy = MagicMock()
        mock_manager = MagicMock()
        mock_setup_swarm.return_value = (mock_proxy, mock_manager)

        main()

        mock_setup_swarm.assert_called_once()
        mock_proxy.initiate_chat.assert_called_once()
        
        args, kwargs = mock_proxy.initiate_chat.call_args
        assert args[0] == mock_manager, "Chat must be initiated with the swarm manager."
        assert "message" in kwargs, "An initial incident message must be provided."
        assert "Test OOM crash" in kwargs["message"], "The message should contain the CLI incident."


    @patch("use_cases.a2a_protocols.src.main.setup_swarm")
    @patch("use_cases.a2a_protocols.src.main.sys.exit")
    @patch("use_cases.a2a_protocols.src.main.argparse.ArgumentParser.parse_args")
    def test_2_main_handles_initialization_error(self, mock_parse_args, mock_sys_exit, mock_setup_swarm):
        """Test 2: Validates that if setup_swarm fails, the system exits gracefully with status code 1."""
        mock_args = argparse.Namespace(incident="Test incident")
        mock_parse_args.return_value = mock_args
        
        mock_setup_swarm.side_effect = Exception("Missing Azure API Key")
        mock_sys_exit.side_effect = SystemExit

        with pytest.raises(SystemExit):
            main()

        mock_sys_exit.assert_called_once_with(1)


    @patch("use_cases.a2a_protocols.src.swarm_setup.os.getenv")
    @patch("use_cases.a2a_protocols.src.swarm_setup.autogen.agentchat.register_function")
    def test_3_setup_swarm_configuration_and_tools(self, mock_register_func, mock_getenv):
        """Test 3: Verifies that setup_swarm structures the LLM config and registers the 3 tools."""
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
        
        # Verify tools are registered exactly 3 times (VRAM, System CPU, Docker logs)
        assert mock_register_func.call_count == 3, "All three diagnostic tools must be registered."


    def test_4_agent_definitions_and_tool_awareness(self):
        """Test 4: Ensures the agents have the new tool-awareness constraints and roles."""
        assert software_agent.name == "Software_Engineer"
        assert hardware_agent.name == "Hardware_Specialist"
        assert architect_agent.name == "Chief_Architect"

        # Check for tool delegation rules
        assert "TOOL DELEGATION" in software_agent.system_message
        assert "PROACTIVE TOOL USE" in hardware_agent.system_message
        
        # Check Architect's new Client-Facing role
        assert "ONLY agent allowed to present" in architect_agent.system_message


    def test_5_user_proxy_behavior(self):
        """Test 5: Verifies the UserProxy dynamic execution path and termination logic."""
        # Verify code execution path uses the dynamic absolute path
        assert "workspace" in user_proxy._code_execution_config["work_dir"]

        # Test standard termination logic
        normal_msg = {"content": "Checking VRAM tools..."}
        assert not user_proxy._is_termination_msg(normal_msg)

        term_msg = {"content": "This concludes the session. TERMINATE"}
        assert user_proxy._is_termination_msg(term_msg)