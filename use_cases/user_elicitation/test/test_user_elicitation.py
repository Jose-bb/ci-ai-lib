import os
import sys
import pytest
from unittest.mock import patch
from pydantic import BaseModel

# Ensure the root directory is in the path to allow absolute imports
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from use_cases.user_elicitation.src.deployment_agent import my_elicitation_handler, main

class MockConfirmationResponse(BaseModel):
    """A mockup of the Pydantic model expected by the server during elicitation."""
    is_confirmed: bool
    reason: str


@pytest.mark.asyncio
@patch('builtins.input', side_effect=['yes', 'Authorized by testing suite'])
async def test_elicitation_handler_approves_deployment(mock_input):
    """Test 1: Verifies that the FastMCP handler correctly processes a human 'yes'."""
    result = await my_elicitation_handler(
        message="Simulated: Deploy model?",
        response_type=MockConfirmationResponse,
        params=None,
        context=None
    )
    
    assert result.action == "accept"
    assert result.content is not None
    assert result.content.is_confirmed is True
    assert result.content.reason == "Authorized by testing suite"


@pytest.mark.asyncio
@patch('builtins.input', side_effect=['no', 'Risk of failure detected'])
async def test_elicitation_handler_blocks_deployment(mock_input):
    """Test 2: Verifies that the FastMCP handler correctly processes a human 'no'."""
    result = await my_elicitation_handler(
        message="Simulated: Deploy model?",
        response_type=MockConfirmationResponse,
        params=None,
        context=None
    )
    
    assert result.action == "accept" 
    assert result.content is not None
    assert result.content.is_confirmed is False
    assert result.content.reason == "Risk of failure detected"


@pytest.mark.asyncio
@patch('builtins.input', side_effect=['invalid_word'])
async def test_elicitation_handler_invalid_input(mock_input):
    """Test 3: Verifies that an unrecognized input cancels the operation directly."""
    result = await my_elicitation_handler(
        message="Simulated: Deploy model?",
        response_type=MockConfirmationResponse,
        params=None,
        context=None
    )
    
    # If the user types gibberish, the handler should immediately return 'cancel'
    assert result.action == "cancel"


@pytest.mark.asyncio
@patch('use_cases.user_elicitation.src.deployment_agent.AzureChatOpenAI')
@patch('builtins.input', side_effect=['quit'])
async def test_agent_graceful_exit(mock_input, mock_llm_class):
    """
    Test 4: Verifies the CLI exits gracefully on the 'quit' command.
    We mock AzureChatOpenAI to prevent real API calls and ensure the test runs instantly.
    """
    # Await the main function; it should start, read 'quit', and break the while loop
    await main()
    
    # Verify that the simulated user actually typed 'quit'
    mock_input.assert_called_once()