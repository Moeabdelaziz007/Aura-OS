import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import json
import struct

from agent.orchestrator.main import AetherCoreOrchestrator

class TestHybridAccessibility(unittest.IsolatedAsyncioTestCase):
    async def test_hybrid_check_with_nodes(self):
        # Mock dependencies
        with patch('agent.orchestrator.main.GeminiLiveClient') as MockGemini:
            mock_gemini_instance = MockGemini.return_value
            mock_gemini_instance.connect = AsyncMock()
            mock_gemini_instance.listen = MagicMock()
            # Mock listen to be an empty async generator
            async def empty_listen():
                if False: yield {}
            mock_gemini_instance.listen.side_effect = empty_listen

            mock_gemini_instance.send_text = AsyncMock()
            mock_gemini_instance.stream_input = AsyncMock()
            mock_gemini_instance.close = AsyncMock()

            orchestrator = AetherCoreOrchestrator()
            # Prevent boot sequence from doing real work
            orchestrator.bridge = MagicMock()
            orchestrator.bridge.load_dna_async = AsyncMock(return_value=MagicMock(version="1.0"))

            # Create a mock websocket
            mock_ws = AsyncMock()
            mock_ws.remote_address = ("127.0.0.1", 12345)

            # Prepare a message with nodes
            metadata = {
                "nodes": [{"role": "button", "name": "Test Button"}],
                # No timestamp_edge so no drift check
            }
            metadata_json = json.dumps(metadata).encode('utf-8')
            metadata_len = len(metadata_json)

            # Header 0x01 (Visual Delta)
            # Packet: [0x01][4 bytes len][metadata][jpeg]
            payload = bytearray([0x01])
            payload.extend(struct.pack('<I', metadata_len))
            payload.extend(metadata_json)
            payload.extend(b'\xff\xd8\xff\xe0') # Fake JPEG header

            # Mock websocket iteration
            mock_ws.__aiter__.return_value = [bytes(payload)]

            # Run the handler
            await orchestrator.handle_optic_nerve(mock_ws)

            # Verification
            mock_gemini_instance.send_text.assert_called_once()
            args, _ = mock_gemini_instance.send_text.call_args
            self.assertIn("Accessibility Context:", args[0])
            self.assertIn("Test Button", args[0])

            mock_gemini_instance.stream_input.assert_not_called()

    async def test_hybrid_check_without_nodes(self):
        # Mock dependencies
        with patch('agent.orchestrator.main.GeminiLiveClient') as MockGemini:
            mock_gemini_instance = MockGemini.return_value
            mock_gemini_instance.connect = AsyncMock()
            mock_gemini_instance.listen = MagicMock()
            async def empty_listen():
                if False: yield {}
            mock_gemini_instance.listen.side_effect = empty_listen

            mock_gemini_instance.send_text = AsyncMock()
            mock_gemini_instance.stream_input = AsyncMock()
            mock_gemini_instance.close = AsyncMock()

            orchestrator = AetherCoreOrchestrator()
            orchestrator.bridge = MagicMock()
            orchestrator.bridge.load_dna_async = AsyncMock(return_value=MagicMock(version="1.0"))

            mock_ws = AsyncMock()
            mock_ws.remote_address = ("127.0.0.1", 12345)

            # Metadata WITHOUT nodes
            metadata = {
                "foo": "bar"
            }
            metadata_json = json.dumps(metadata).encode('utf-8')
            metadata_len = len(metadata_json)

            payload = bytearray([0x01])
            payload.extend(struct.pack('<I', metadata_len))
            payload.extend(metadata_json)
            payload.extend(b'\xff\xd8\xff\xe0')

            mock_ws.__aiter__.return_value = [bytes(payload)]

            await orchestrator.handle_optic_nerve(mock_ws)

            # Verification
            mock_gemini_instance.send_text.assert_not_called()
            mock_gemini_instance.stream_input.assert_called_once()

if __name__ == '__main__':
    unittest.main()
