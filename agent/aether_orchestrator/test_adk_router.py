import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import sys

from agent.aether_orchestrator.adk_router import ADKRouter

class TestADKRouter(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        """Set up the test environment for each test."""
        self.mock_bridge = MagicMock()
        # Setup async methods on the mock bridge
        self.mock_bridge.execute_tool = AsyncMock()
        self.mock_bridge.trigger_swarm = AsyncMock()

        self.router = ADKRouter(self.mock_bridge)

    async def test_route_system_1_reflex(self):
        """Test routing to System 1 (Reflexive) with execute_tool available."""
        context = {
            "system": "SYSTEM_1_REFLEX",
            "action": "click",
            "params": {"x": 100, "y": 200}
        }
        self.mock_bridge.execute_tool.return_value = "Tool Executed"

        result = await self.router.route_action(context)

        self.mock_bridge.execute_tool.assert_awaited_once_with("click", x=100, y=200)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["output"], "Tool Executed")
        self.assertEqual(result["system"], "SYSTEM_1_REFLEX")
        self.assertEqual(result["action"], "click")

    async def test_route_system_1_reflex_fallback(self):
        """Test routing to System 1 when execute_tool is missing on bridge."""
        # Create a bridge without execute_tool
        bridge = MagicMock(spec=[])
        router = ADKRouter(bridge)

        context = {
            "system": "SYSTEM_1_REFLEX",
            "action": "click",
            "params": {}
        }

        result = await router.route_action(context)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["output"], "System 1 executed: click")
        self.assertEqual(result["system"], "SYSTEM_1_REFLEX")

    async def test_route_system_2_swarm(self):
        """Test routing to System 2 (Swarm) with trigger_swarm available."""
        context = {
            "system": "SYSTEM_2_SWARM",
            "action": "analyze",
            "params": {"target": "image.png"}
        }
        self.mock_bridge.trigger_swarm.return_value = "Swarm Result"

        result = await self.router.route_action(context)

        self.mock_bridge.trigger_swarm.assert_awaited_once_with("analyze", target="image.png")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["output"], "Swarm Result")
        self.assertEqual(result["system"], "SYSTEM_2_SWARM")

    async def test_route_system_2_swarm_fallback(self):
        """Test routing to System 2 when trigger_swarm is missing on bridge."""
        bridge = MagicMock(spec=[])
        router = ADKRouter(bridge)

        context = {
            "system": "SYSTEM_2_SWARM",
            "action": "analyze",
            "params": {}
        }

        result = await router.route_action(context)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["output"], "System 2 swarm simulated: analyze")
        self.assertEqual(result["system"], "SYSTEM_2_SWARM")

    async def test_unknown_system(self):
        """Test routing with an unknown system."""
        context = {
            "system": "UNKNOWN_SYSTEM",
            "action": "test"
        }

        result = await self.router.route_action(context)

        self.assertEqual(result["status"], "error")
        self.assertIn("Unknown system", result["error"])
        self.mock_bridge.execute_tool.assert_not_called()
        self.mock_bridge.trigger_swarm.assert_not_called()

    async def test_exception_handling(self):
        """Test exception handling during routing."""
        context = {
            "system": "SYSTEM_1_REFLEX",
            "action": "fail",
            "params": {}
        }
        self.mock_bridge.execute_tool.side_effect = Exception("Bridge Failure")

        result = await self.router.route_action(context)

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "Bridge Failure")

    async def test_missing_params_default(self):
        """Test routing when 'params' key is missing in context."""
        context = {
            "system": "SYSTEM_1_REFLEX",
            "action": "default_params"
            # params missing
        }
        self.mock_bridge.execute_tool.return_value = "OK"

        result = await self.router.route_action(context)

        self.mock_bridge.execute_tool.assert_awaited_once_with("default_params")
        self.assertEqual(result["output"], "OK")

    async def test_empty_params(self):
        """Test routing when 'params' is an empty dict."""
        context = {
            "system": "SYSTEM_1_REFLEX",
            "action": "empty_params",
            "params": {}
        }
        self.mock_bridge.execute_tool.return_value = "OK"

        result = await self.router.route_action(context)

        self.mock_bridge.execute_tool.assert_awaited_once_with("empty_params")
        self.assertEqual(result["output"], "OK")

    async def test_invalid_params_type(self):
        """Test robustness when params is None (which causes **None TypeError)."""
        context = {
            "system": "SYSTEM_1_REFLEX",
            "action": "bad_params",
            "params": None
        }
        # This will raise TypeError: argument after ** must be a mapping, not NoneType
        # The router should catch this and return an error result

        result = await self.router.route_action(context)

        self.assertEqual(result["status"], "error")
        self.assertIn("argument after ** must be a mapping", str(result["error"]))

if __name__ == "__main__":
    unittest.main()
