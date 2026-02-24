import pytest
from unittest.mock import AsyncMock, Mock, patch
import json
# Patching the class BEFORE importing or instantiating could be tricky if import fails.
# But import works now.
from agent.aether_forge.motor_cortex import AetherMotorCortex
from agent.aether_forge.aether_forge import AetherForge

# Monkeypatch the broken class - Wait, the class has _execute_api_request, but test uses aether_execute_api_request
# The test was likely written for an older version of the class or vice-versa.
# I should fix the test to call the correct method if I'm not supposed to monkeypatch.
# But the error message says `type object 'AetherMotorCortex' has no attribute 'aether_execute_api_request'`
# which implies the test code attempts to access `AetherMotorCortex.aether_execute_api_request` to assign it to `_execute_api_request`.
# That means `aether_execute_api_request` does NOT exist in the class.
# The class definition shows `_execute_api_request`.
# So the monkeypatch lines themselves are the cause of the error if they run at module level.

@pytest.fixture
def mock_forge():
    # Mock AetherForge to avoid async init issues
    mock = Mock(spec=AetherForge)
    # Ensure __init__ doesn't run if we subclass, but here we pass it as arg
    return mock

@pytest.mark.asyncio
async def test_dispatch_known_tool(mock_forge):
    cortex = AetherMotorCortex(forge=mock_forge)

    # Mock the internal methods we just patched
    cortex._execute_api_request = AsyncMock(return_value={"success": True})
    # We need to update tools dict because it was initialized with the UNBOUND methods
    # Wait, if I patch the class, __init__ will use the patched methods.

    # Re-initialize tools to point to the mock
    cortex.tools["execute_api_request"] = cortex._execute_api_request

    result = await cortex.dispatch("execute_api_request", {"service": "coingecko"})

    assert result == {"success": True}
    cortex._execute_api_request.assert_called_once_with({"service": "coingecko"})

@pytest.mark.asyncio
async def test_dispatch_unknown_tool(mock_forge):
    cortex = AetherMotorCortex(forge=mock_forge)
    result = await cortex.dispatch("unknown_tool", {})
    assert "error" in result
    assert "unknown to the Motor Cortex" in result["error"]

@pytest.mark.asyncio
async def test_execute_api_missing_service(mock_forge):
    cortex = AetherMotorCortex(forge=mock_forge)

    # Use the correct method name
    result = await cortex._execute_api_request({})
    assert result == {"error": "Missing 'service' parameter. Use: coingecko, github, weather"}

@pytest.mark.asyncio
async def test_manipulate_dom(mock_forge):
    cortex = AetherMotorCortex(forge=mock_forge)
    # Use the correct method name
    result = await cortex._manipulate_dom({"element_id": "btn-1", "action": "click"})
    assert result["success"] is True
    assert "Executed 'click'" in result["message"]
