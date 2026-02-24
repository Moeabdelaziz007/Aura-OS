import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock
from agent.aether_forge.motor_cortex import AetherMotorCortex

class TestMotorCortex(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_forge = MagicMock()
        self.mock_forge.forge_and_deploy = AsyncMock()
        self.motor = AetherMotorCortex(forge=self.mock_forge)

    async def test_api_request_dispatch(self):
        print("🦾 Testing API Request Dispatch...")
        
        # Mock result
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.service = "coingecko"
        mock_result.data = {"BITCOIN": "66k"}
        mock_result.ascii_visual = "Visual Data"
        self.mock_forge.forge_and_deploy.return_value = mock_result

        args = {"service": "coingecko", "params": {"coins": ["bitcoin"]}}
        response = await self.motor.dispatch("execute_api_request", args)

        self.assertTrue(response["success"])
        self.assertEqual(response["service"], "coingecko")
        self.mock_forge.forge_and_deploy.assert_called_once()
        print("✅ API Dispatch verified.")

    async def test_dom_dispatch(self):
        print("🖱️ Testing DOM Manipulation Dispatch...")
        args = {"element_id": "buy_btn", "action": "click"}
        response = await self.motor.dispatch("manipulate_dom", args)
        
        self.assertTrue(response["success"])
        self.assertIn("buy_btn", response["message"])
        print("✅ DOM Dispatch verified.")

    async def test_unknown_tool(self):
        print("🚫 Testing Unknown Tool handling...")
        response = await self.motor.dispatch("invalid_tool", {})
        self.assertIn("error", response)
        print("✅ Error handling verified.")

if __name__ == "__main__":
    unittest.main()
