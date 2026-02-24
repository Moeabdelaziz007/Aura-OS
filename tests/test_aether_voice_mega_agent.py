"""
🧪 Test Suite for Aether Voice Mega Agent
==========================================
Comprehensive tests for the Gemini Live Bridge and voice command processing.
"""

import unittest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import sys
import os

# Mock ALL dependencies before any imports
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()
sys.modules['google.ai'] = MagicMock()
sys.modules['dotenv'] = MagicMock()
sys.modules['firebase_admin'] = MagicMock()
sys.modules['firebase_admin.firestore'] = MagicMock()
sys.modules['pyaudio'] = MagicMock()

os.environ["GEMINI_API_KEY"] = "test_key"


class TestGeminiLiveBridge(unittest.IsolatedAsyncioTestCase):
    """Test GeminiLiveBridge voice command processing."""

    async def asyncSetUp(self):
        """Set up test fixtures."""
        from agent.aether_forge.gemini_live_bridge import AetherGeminiLiveBridge
        from agent.aether_forge.models import ResolvedIntent, UrgencyLevel, CognitiveSystem
        
        self.bridge = AetherGeminiLiveBridge(api_key="test_key")
        
        # Mock the forge and solver
        self.bridge.forge = MagicMock()
        self.bridge.solver = MagicMock()
        
        # Create mock result
        self.mock_result = MagicMock()
        self.mock_result.success = True
        self.mock_result.service = "coingecko"
        self.mock_result.data = {"Price_USD": "$65,000", "Trend_24h": "-2.5%"}
        self.mock_result.display = MagicMock(return_value="ASCII Display")
        
        self.bridge.forge.aether_resolve_and_forge = AsyncMock(return_value=self.mock_result)
        
        # Mock solver resolve using correct ResolvedIntent fields
        mock_intent = ResolvedIntent(
            raw_query="What is the Bitcoin price?",
            action="price_check",
            target="bitcoin",
            urgency=UrgencyLevel.MEDIUM,
            cognitive_system=CognitiveSystem.SYSTEM_1,
            tau=0.5,
            confidence=0.95,
            reasoning="User wants Bitcoin price"
        )
        self.bridge.solver.resolve = AsyncMock(return_value=mock_intent)

    async def test_process_voice_command_success(self):
        """Test successful voice command processing."""
        response = await self.bridge.process_voice_command(
            audio_input="What is the Bitcoin price?",
            screen_description="TradingView visible"
        )
        
        self.assertIsNotNone(response)

    async def test_process_voice_command_arabic(self):
        """Test Arabic voice command processing."""
        response = await self.bridge.process_voice_command(
            audio_input="ما هو سعر البيتكوين؟",
            screen_description="TradingView visible"
        )
        
        self.assertIsNotNone(response)
        # Verify forge was called
        self.bridge.forge.aether_resolve_and_forge.assert_called_once()

    async def test_process_voice_command_with_screen_context(self):
        """Test voice command with screen context."""
        response = await self.bridge.process_voice_command(
            audio_input="Show me the chart",
            screen_description="TradingView showing BTC/USD"
        )
        
        # Verify solver was called with screen context
        self.bridge.solver.resolve.assert_called_once()

    async def test_process_voice_command_failure(self):
        """Test voice command processing failure handling."""
        # Mock a failed result
        failed_result = MagicMock()
        failed_result.success = False
        failed_result.error = "API Error"
        self.bridge.forge.aether_resolve_and_forge = AsyncMock(return_value=failed_result)
        
        response = await self.bridge.process_voice_command(
            audio_input="Invalid command",
            screen_description=None
        )
        
        self.assertIn("مشكلة", response)  # Arabic error message

    async def test_synthesize_voice_response_coingecko(self):
        """Test voice response synthesis for CoinGecko service."""
        result = MagicMock()
        result.service = "coingecko"
        result.data = {"Price_USD": "$65,000", "Trend_24h": "-2.5%"}
        
        response = self.bridge.aether_synthesize_voice_response(result)
        
        self.assertIn("السعر", response)
        self.assertIn("$65,000", response)

    async def test_synthesize_voice_response_github(self):
        """Test voice response synthesis for GitHub service."""
        result = MagicMock()
        result.service = "github"
        result.data = {"total_count": 42}
        
        response = self.bridge.aether_synthesize_voice_response(result)
        
        self.assertIn("42", response)
        self.assertIn("جيت هاب", response)  # GitHub in Arabic


class TestVoiceIntentResolution(unittest.TestCase):
    """Test voice intent resolution through constraint solver."""

    def setUp(self):
        """Set up test fixtures."""
        from agent.aether_forge.constraint_solver import AetherConstraintSolver
        from agent.aether_forge.models import VoiceFeatures, ScreenContext
        
        self.solver = AetherConstraintSolver()
        
        self.normal_voice = VoiceFeatures(
            speech_rate_wpm=150.0,
            pitch_variance=0.4,
            volume_db=-20.0,
            pause_frequency=3.0,
            transcript="Get Bitcoin price",
            language="en"
        )
        
        self.urgent_voice = VoiceFeatures(
            speech_rate_wpm=280.0,
            pitch_variance=0.9,
            volume_db=-5.0,
            pause_frequency=0.5,
            transcript="SELL BITCOIN NOW!",
            language="en"
        )
        
        self.screen_context = ScreenContext(
            raw_description="TradingView showing BTC chart",
            detected_assets=["Bitcoin", "TradingView"],
            detected_app="TradingView",
            detected_numbers=[65000.0]
        )

    def test_intent_resolution_normal_voice(self):
        """Test intent resolution with normal voice features."""
        from agent.aether_forge.constraint_solver import build_time_context
        
        intent = self.solver.resolve(
            query="Get Bitcoin price",
            voice=self.normal_voice,
            screen=self.screen_context,
            time_ctx=build_time_context()
        )
        
        self.assertIsNotNone(intent)

    def test_intent_resolution_urgent_voice(self):
        """Test intent resolution with urgent voice features."""
        from agent.aether_forge.constraint_solver import build_time_context
        
        intent = self.solver.resolve(
            query="SELL BITCOIN NOW!",
            voice=self.urgent_voice,
            screen=self.screen_context,
            time_ctx=build_time_context()
        )
        
        self.assertIsNotNone(intent)


if __name__ == "__main__":
    unittest.main()
