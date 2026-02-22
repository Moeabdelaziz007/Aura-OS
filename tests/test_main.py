import unittest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import json
import os
import time

# Set dummy API key to avoid error during initialization
os.environ["GEMINI_API_KEY"] = "dummy_key"

from agent.orchestrator.main import AetherCoreOrchestrator, GeminiLiveClient

class TestOrchestrator(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Mock dependencies before creating orchestrator
        with patch('agent.orchestrator.main.AuraNavigator') as MockNav:
            self.mock_nav = MockNav.return_value
            self.mock_nav.load_dna_async = AsyncMock()
            self.mock_nav.load_dna_async.return_value = MagicMock(version="0.0.0")

            with patch('agent.orchestrator.main.HyperMindRouter') as MockRouter:
                self.mock_router = MockRouter.return_value

                self.orchestrator = AetherCoreOrchestrator()
                self.orchestrator.bridge = self.mock_nav
                self.orchestrator.router = self.mock_router

    @patch('agent.orchestrator.main.GeminiLiveClient')
    async def test_handle_optic_nerve_raw_jpeg(self, MockGemini):
        # Mock WebSocket
        websocket = AsyncMock()
        websocket.remote_address = ("127.0.0.1", 12345)

        # Create raw JPEG payload: header (0x01) + FF D8 (Start of Image) + dummy data
        raw_jpeg = b'\xFF\xD8\xFF\xE0'
        message = b'\x01' + raw_jpeg

        # Setup websocket to return message then stop iteration
        websocket.__aiter__.return_value = [message]

        # Mock Gemini client instance
        gemini_instance = MockGemini.return_value
        gemini_instance.connect = AsyncMock()
        gemini_instance.listen = MagicMock()
        gemini_instance.listen.return_value.__aiter__.return_value = [] # Empty generator
        gemini_instance.stream_input = AsyncMock()
        gemini_instance.close = AsyncMock()

        # Run handle_optic_nerve
        try:
            await asyncio.wait_for(self.orchestrator.handle_optic_nerve(websocket), timeout=1.0)
        except asyncio.TimeoutError:
            pass

        gemini_instance.stream_input.assert_called()
        args, _ = gemini_instance.stream_input.call_args
        self.assertEqual(args[0], raw_jpeg)

    @patch('agent.orchestrator.main.GeminiLiveClient')
    async def test_handle_optic_nerve_metadata_jpeg(self, MockGemini):
        # Mock WebSocket
        websocket = AsyncMock()
        websocket.remote_address = ("127.0.0.1", 12345)

        # Create metadata payload with current timestamp to avoid drift
        # The drift check is: (orchestrator_time - edge_time) / 1_000_000 > 500ms
        # We need edge_time to be close to orchestrator_time (which is time.time_ns())
        # So we set edge_time to current time
        metadata = {"timestamp_edge": time.time_ns()}
        metadata_bytes = json.dumps(metadata).encode("utf-8")
        metadata_len = len(metadata_bytes).to_bytes(4, "little")
        jpeg_data = b'\xFF\xD8\xFF\xE0'

        # Construct message: header (0x01) + len + metadata + jpeg
        message = b'\x01' + metadata_len + metadata_bytes + jpeg_data

        # Setup websocket
        websocket.__aiter__.return_value = [message]

        # Mock Gemini client instance
        gemini_instance = MockGemini.return_value
        gemini_instance.connect = AsyncMock()
        gemini_instance.listen = MagicMock()
        gemini_instance.listen.return_value.__aiter__.return_value = []
        gemini_instance.stream_input = AsyncMock()
        gemini_instance.close = AsyncMock()

        # Run handle_optic_nerve
        try:
            await asyncio.wait_for(self.orchestrator.handle_optic_nerve(websocket), timeout=1.0)
        except asyncio.TimeoutError:
            pass

        # Verify stream_input was called with the JPEG data
        gemini_instance.stream_input.assert_called()
        args, _ = gemini_instance.stream_input.call_args
        self.assertEqual(args[0], jpeg_data)

    @patch('agent.orchestrator.main.GeminiLiveClient')
    async def test_handle_optic_nerve_drift_detected(self, MockGemini):
        # Set a small drift threshold for testing
        self.orchestrator.drift_threshold_ms = 100.0

        # Mock WebSocket
        websocket = AsyncMock()
        websocket.remote_address = ("127.0.0.1", 12345)

        # Create metadata payload with old timestamp to simulate drift
        # 200ms drift (which is > 100ms threshold)
        old_time = time.time_ns() - 200 * 1_000_000
        metadata = {"timestamp_edge": old_time}
        metadata_bytes = json.dumps(metadata).encode("utf-8")
        metadata_len = len(metadata_bytes).to_bytes(4, "little")
        jpeg_data = b'\xFF\xD8\xFF\xE0'

        # Construct message: header (0x01) + len + metadata + jpeg
        message = b'\x01' + metadata_len + metadata_bytes + jpeg_data

        # Setup websocket
        websocket.__aiter__.return_value = [message]

        # Mock Gemini client instance
        gemini_instance = MockGemini.return_value
        gemini_instance.connect = AsyncMock()
        gemini_instance.listen = MagicMock()
        gemini_instance.listen.return_value.__aiter__.return_value = []
        gemini_instance.stream_input = AsyncMock()
        gemini_instance.close = AsyncMock()

        # Run handle_optic_nerve
        try:
            await asyncio.wait_for(self.orchestrator.handle_optic_nerve(websocket), timeout=1.0)
        except asyncio.TimeoutError:
            pass

        # Verify stream_input was NOT called due to drift
        gemini_instance.stream_input.assert_not_called()

if __name__ == '__main__':
    unittest.main()
