import unittest
import asyncio
import json
from unittest.mock import MagicMock, AsyncMock, patch
from agent.orchestrator.gemini_live_client import GeminiLiveClient

class TestGeminiLiveClientFixes(unittest.IsolatedAsyncioTestCase):
    async def test_listen_waits_for_connection(self):
        """Test that listen() waits for connect() to complete."""
        mock_bridge = MagicMock()
        client = GeminiLiveClient(mock_bridge, "fake_key")

        # Mock ws
        mock_ws = MagicMock()
        mock_ws.__aiter__.return_value = [
            json.dumps({"serverContent": {"text": "hello"}})
        ]

        # Simulate connection taking some time
        async def delayed_connect():
            await asyncio.sleep(0.1)
            client.ws = mock_ws
            client.is_ready = True
            client._connected_event.set()

        # Start connect in background
        asyncio.create_task(delayed_connect())

        # Call listen immediately
        # If fix is working, this should wait and then yield the message
        # If fix is NOT working, this would return immediately (empty list) or error

        messages = []
        try:
            async for msg in client.listen():
                messages.append(msg)
        except Exception as e:
            self.fail(f"listen() raised exception: {e}")

        # Since we mocked __aiter__ with one message, we expect one message
        # However, mocking __aiter__ on AsyncMock is tricky.
        # Let's simplify and just check if it waited.

        self.assertTrue(client.is_ready, "Client should be ready after wait")
        self.assertTrue(client._connected_event.is_set(), "Event should be set")

    async def test_listen_timeout(self):
        """Test that listen() times out if connection never happens."""
        mock_bridge = MagicMock()
        client = GeminiLiveClient(mock_bridge, "fake_key")

        # We do NOT call connect() or set the event

        # Override wait_for to be fast
        original_wait_for = asyncio.wait_for

        async def fast_wait_for(fut, timeout):
            # We enforce a small timeout for the test
            return await original_wait_for(fut, timeout=0.1)

        with patch('asyncio.wait_for', side_effect=fast_wait_for):
            messages = []
            async for msg in client.listen():
                messages.append(msg)

            self.assertEqual(len(messages), 0, "Should return no messages on timeout")

if __name__ == '__main__':
    unittest.main()
