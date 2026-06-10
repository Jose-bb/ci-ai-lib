import os
import sys
import pytest
import asyncio
import warnings
from unittest.mock import patch, MagicMock, AsyncMock

# Eliminate flaml's harmless warning
warnings.filterwarnings("ignore", category=UserWarning, module="flaml")

# Ensure the root directory is accessible for absolute imports
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from use_cases.a2a_protocols.src.agents import (
    software_agent, hardware_agent, architect_agent, 
    WebSocketUserProxyAgent, telemetry_hook
)
from use_cases.a2a_protocols.utilities.cost_tracker import calculate_turn_cost

class TestA2AProtocolsV3:
    """
    Test suite for the A2A Protocols setup (V3).
    Validates async WebSockets, HITL concurrency locks, and Telemetry Cost calculation.
    """

    def test_1_cost_tracker_calculations(self):
        """Test 1: Validates the token cost math for lightweight models like gpt-4o-mini."""
        # 1000 prompt tokens = $0.00015 | 1000 completion tokens = $0.00060
        cost = calculate_turn_cost(prompt_tokens=1000, completion_tokens=1000, model_name="gpt-4o-mini")
        assert cost == 0.00075, "The math for gpt-4o-mini pricing must be exact."

        # Unknown models should default to the mini pricing
        cost_default = calculate_turn_cost(1000, 1000, "unknown_model")
        assert cost_default == 0.00075, "Unknown models should fallback to the default rates."


    @pytest.mark.asyncio
    async def test_2_websocket_user_proxy_human_input(self):
        """Test 2: Verifies that the custom proxy uses the websocket to ask for human input."""
        proxy = WebSocketUserProxyAgent(name="test_proxy")
        
        # Mock the async WebSocket connection
        mock_ws = AsyncMock()
        mock_ws.receive_json.return_value = {"content": "y"}
        proxy.websocket = mock_ws

        # Trigger the human input method
        response = await proxy.a_get_human_input("Do you approve this execution?")
        
        # Verify the outgoing request payload
        mock_ws.send_json.assert_called_once()
        args, kwargs = mock_ws.send_json.call_args
        assert args[0]["type"] == "human_input_request"
        assert args[0]["prompt"] == "Do you approve this execution?"
        
        # Verify the incoming parsing
        assert response == "y", "The proxy should extract and return the 'content' key from the JSON."


    @pytest.mark.asyncio
    async def test_3_telemetry_hook_broadcasts_cost(self):
        """Test 3: Ensures the middleware extracts tokens and sends telemetry without modifying the message."""
        # Setup a mock sender representing an AutoGen agent with usage stats
        mock_sender = MagicMock()
        mock_sender.name = "Test_Agent"
        mock_sender.client.actual_usage_summary = {
            "gpt-4o-mini": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            }
        }

        # Mock the global user_proxy's websocket
        mock_ws = AsyncMock()
        
        with patch("use_cases.a2a_protocols.src.agents.user_proxy") as mock_user_proxy:
            mock_user_proxy.websocket = mock_ws
            
            original_message = {"content": "This is an important AI message."}
            
            # Execute the hook
            returned_message = telemetry_hook(
                sender=mock_sender,
                message=original_message,
                recipient=MagicMock(),
                silent=False
            )

            # CRITICAL: The hook must return the exact same message to not break the chat flow
            assert returned_message == original_message
            
            # Yield control to the event loop so the asyncio.create_task has time to execute
            await asyncio.sleep(0.01)
            
            # Validate the telemetry broadcast payload
            mock_ws.send_json.assert_called_once()
            args, kwargs = mock_ws.send_json.call_args
            assert args[0]["type"] == "status"
            assert "[TELEMETRY]" in args[0]["content"]
            assert "150 tokens" in args[0]["content"]


    def test_4_agent_definitions_and_hooks_registered(self):
        """Test 4: Verifies the core agents exist and have the telemetry hook registered."""
        assert software_agent.name == "Software_Engineer"
        assert hardware_agent.name == "Hardware_Specialist"
        assert architect_agent.name == "Chief_Architect"

        # Verify that the middleware is actively attached to the pre-send event
        assert len(software_agent.hook_lists["process_message_before_send"]) > 0, "Telemetry hook missing on Software Agent"
        assert len(architect_agent.hook_lists["process_message_before_send"]) > 0, "Telemetry hook missing on Architect Agent"