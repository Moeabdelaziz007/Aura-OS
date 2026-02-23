
import unittest
from unittest.mock import AsyncMock, patch, MagicMock, call
import asyncio
import json
import struct
import os
import time
import sys

# Mock missing dependencies
mock_pydantic = MagicMock()
class MockBaseModel:
    def __init__(self, **data):
        # Handle nested models based on annotations
        annotations = getattr(self, '__annotations__', {})
        for k, v in data.items():
            if k in annotations and isinstance(v, dict):
                field_type = annotations[k]
                # Handle optional or union types if necessary, but keep it simple for now
                if isinstance(field_type, type) and issubclass(field_type, MockBaseModel):
                    v = field_type(**v)
            setattr(self, k, v)
    def dict(self):
        d = {}
        for k, v in self.__dict__.items():
            if isinstance(v, MockBaseModel):
                d[k] = v.dict()
            else:
                d[k] = v
        return d
    def model_dump(self): return self.dict()
    class Config: extra = "allow"
mock_pydantic.BaseModel = MockBaseModel
mock_pydantic.Field = MagicMock(return_value=MagicMock())
mock_pydantic.ValidationError = type("ValidationError", (Exception,), {})
sys.modules["pydantic"] = mock_pydantic
sys.modules["websockets"] = MagicMock()
sys.modules["dotenv"] = MagicMock()
sys.modules["numpy"] = MagicMock()
# sys.modules["google"] = MagicMock()  # This breaks firebase_admin
sys.modules["google.generativeai"] = MagicMock()

# We need to set the environment variable before importing main so it picks it up
os.environ["GEMINI_API_KEY"] = "test_api_key"

from agent.orchestrator.main import AetherCoreOrchestrator, SynapticMessage, ActionContext

class AsyncIterator:
    def __init__(self, items, delay=0):
        self.items = items
        self.index = 0
        self.delay = delay

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.delay > 0:
            await asyncio.sleep(self.delay)
        if self.index < len(self.items):
            item = self.items[self.index]
            self.index += 1
            return item
        else:
            raise StopAsyncIteration

class MockWebsocket:
    def __init__(self, messages, remote_address=("127.0.0.1", 12345), delay=0):
        self.messages = messages
        self.remote_address = remote_address
        self.delay = delay
        self.send = AsyncMock()
        self.open = True

    def __aiter__(self):
        return AsyncIterator(self.messages, self.delay)

class TestAetherCoreOrchestrator(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Mock dependencies
        self.mock_gemini_cls = patch('agent.orchestrator.main.GeminiLiveClient').start()
        self.mock_gemini_instance = self.mock_gemini_cls.return_value
        self.mock_gemini_instance.connect = AsyncMock()
        self.mock_gemini_instance.listen.return_value = AsyncIterator([]) # Empty iterator by default
        self.mock_gemini_instance.send_text = AsyncMock()
        self.mock_gemini_instance.stream_input = AsyncMock()
        self.mock_gemini_instance.close = AsyncMock()

        self.mock_router_cls = patch('agent.orchestrator.main.HyperMindRouter').start()
        self.mock_router_instance = self.mock_router_cls.return_value
        self.mock_router_instance.route_action = AsyncMock(return_value="SYSTEM_1_REFLEX")

        self.mock_navigator_cls = patch('agent.orchestrator.main.AetherNavigator').start()
        self.mock_navigator_instance = self.mock_navigator_cls.return_value
        self.mock_navigator_instance.load_dna_async = AsyncMock(return_value=MagicMock(version="1.0.0"))
        self.mock_navigator_instance.close = AsyncMock()

        self.mock_monitor = patch('agent.orchestrator.main.monitor').start()
        self.mock_evolve_engine = patch('agent.orchestrator.main.evolve_engine').start()
        self.mock_evolve_engine.trigger_healing = AsyncMock()

        self.orchestrator = AetherCoreOrchestrator()

    async def asyncTearDown(self):
        patch.stopall()
        await self.orchestrator.shutdown()

    async def test_handle_optic_nerve_raw_jpeg(self):
        # Test raw JPEG (0xFF 0xD8) with header 0x01
        header = b'\x01'
        jpeg_marker = b'\xFF\xD8'
        payload = jpeg_marker + b'\x00' * 10 # Some dummy data
        message = header + payload

        mock_websocket = MockWebsocket([message])

        await self.orchestrator.handle_optic_nerve(mock_websocket)

        # Verify Gemini initialized and connected
        self.mock_gemini_cls.assert_called_once()
        self.mock_gemini_instance.connect.assert_called()

        # Verify stream_input called with correct data
        self.mock_gemini_instance.stream_input.assert_called_with(payload, mime_type="image/jpeg")

    async def test_handle_optic_nerve_metadata_jpeg(self):
        # Test Metadata + JPEG (valid)
        header = b'\x01'
        metadata = {"timestamp_edge": time.time_ns(), "extra": "data"}
        metadata_json = json.dumps(metadata).encode("utf-8")
        metadata_len = len(metadata_json)

        # [4 bytes len][metadata][jpeg]
        payload = struct.pack("<I", metadata_len) + metadata_json + b'\xFF\xD8\x00'
        message = header + payload

        mock_websocket = MockWebsocket([message])

        await self.orchestrator.handle_optic_nerve(mock_websocket)

        # Expect payload passed to stream_input is just the JPEG part
        expected_jpeg = b'\xFF\xD8\x00'
        self.mock_gemini_instance.stream_input.assert_called_with(expected_jpeg, mime_type="image/jpeg")

    async def test_handle_optic_nerve_malformed_metadata(self):
        # Test Metadata + JPEG (invalid JSON)
        header = b'\x01'
        metadata_raw = b"{invalid_json"
        metadata_len = len(metadata_raw)

        payload = struct.pack("<I", metadata_len) + metadata_raw + b'\xFF\xD8\x00'
        message = header + payload

        mock_websocket = MockWebsocket([message])

        await self.orchestrator.handle_optic_nerve(mock_websocket)

        # Should still stream the JPEG payload
        expected_jpeg = b'\xFF\xD8\x00'
        self.mock_gemini_instance.stream_input.assert_called_with(expected_jpeg, mime_type="image/jpeg")

    async def test_handle_optic_nerve_short_payload(self):
        # Payload too short to be meaningful
        header = b'\x01'
        payload = b'\x00' # Length 1, not start with FF D8
        message = header + payload # Total length 2

        mock_websocket = MockWebsocket([message])

        await self.orchestrator.handle_optic_nerve(mock_websocket)

        # stream_input called with empty bytes
        self.mock_gemini_instance.stream_input.assert_called_with(b'', mime_type="image/jpeg")

    async def test_handle_optic_nerve_drift_detection(self):
        # Drift > threshold
        header = b'\x01'
        # Set edge timestamp to 10 seconds ago (10,000 ms), default threshold is 500ms
        edge_time = time.time_ns() - 10 * 1_000_000_000
        metadata = {"timestamp_edge": edge_time}
        metadata_json = json.dumps(metadata).encode("utf-8")
        metadata_len = len(metadata_json)

        payload = struct.pack("<I", metadata_len) + metadata_json + b'\xFF\xD8\x00'
        message = header + payload

        mock_websocket = MockWebsocket([message])

        await self.orchestrator.handle_optic_nerve(mock_websocket)

        # Should NOT call stream_input because of drift
        self.mock_gemini_instance.stream_input.assert_not_called()

    async def test_handle_optic_nerve_hybrid_accessibility(self):
        # Metadata has "nodes"
        header = b'\x01'
        nodes = [{"role": "button", "name": "Submit"}]
        metadata = {"nodes": nodes, "timestamp_edge": time.time_ns()} # valid timestamp
        metadata_json = json.dumps(metadata).encode("utf-8")
        metadata_len = len(metadata_json)

        payload = struct.pack("<I", metadata_len) + metadata_json + b'\xFF\xD8\x00'
        message = header + payload

        mock_websocket = MockWebsocket([message])

        await self.orchestrator.handle_optic_nerve(mock_websocket)

        # Should NOT stream JPEG
        self.mock_gemini_instance.stream_input.assert_not_called()
        # Should send text
        self.mock_gemini_instance.send_text.assert_called()
        args, _ = self.mock_gemini_instance.send_text.call_args
        self.assertIn("Accessibility Context", args[0])

    async def test_handle_optic_nerve_audio_chunk(self):
        # Header 0x02
        header = b'\x02'
        payload = b'\x00\x01\x02'
        message = header + payload

        mock_websocket = MockWebsocket([message])

        await self.orchestrator.handle_optic_nerve(mock_websocket)

        self.mock_gemini_instance.stream_input.assert_called_with(payload, mime_type="audio/pcm")

    async def test_handle_optic_nerve_json_message(self):
        # Valid JSON
        data = {
            "data": {
                "anomaly": 0.1,
                "novelty": 0.5,
                "goal_alignment": 0.9
            }
        }
        message = json.dumps(data)

        mock_websocket = MockWebsocket([message])

        await self.orchestrator.handle_optic_nerve(mock_websocket)

        self.mock_router_instance.route_action.assert_called()
        # Verify call args
        call_args = self.mock_router_instance.route_action.call_args[0][0]
        self.assertEqual(call_args["anomaly"], 0.1)

    async def test_handle_optic_nerve_neural_poison(self):
        data = {
            "data": {
                "poison": "NEURAL_POISON"
            }
        }
        message = json.dumps(data)

        mock_websocket = MockWebsocket([message])

        await self.orchestrator.handle_optic_nerve(mock_websocket)

        # Should log anomaly and NOT route action
        self.mock_monitor.log_anomaly.assert_called_with("Orchestrator", "NeuralPoison", "Poison signal detected and bypassed.")
        self.mock_router_instance.route_action.assert_not_called()

    async def test_handle_optic_nerve_invalid_json(self):
        message = "{invalid_json"

        mock_websocket = MockWebsocket([message])

        await self.orchestrator.handle_optic_nerve(mock_websocket)

        self.mock_monitor.log_anomaly.assert_called_with("SynapticBridge", "ValidationError", "Expecting property name enclosed in double quotes: line 1 column 2 (char 1)")
        self.mock_router_instance.route_action.assert_not_called()

    async def test_listen_to_gemini_spatial_match(self):
        # Setup gemini listen to yield a response
        response = {
            "modelTurn": {
                "parts": [
                    {"text": 'Some text {"point": [500, 500]}'}
                ]
            }
        }
        self.mock_gemini_instance.listen.return_value = AsyncIterator([response])

        # Need a websocket that stays open long enough
        mock_websocket = MockWebsocket([], delay=0.1) # Wait 0.1s then stop

        await self.orchestrator.handle_optic_nerve(mock_websocket)

        # Verify websocket.send called with CLICK action
        # The logic:
        # abs_x = int((500 / 1000.0) * 1920) = 960
        # abs_y = int((500 / 1000.0) * 1080) = 540
        expected_action = {"action": "CLICK", "x": 960, "y": 540}

        # Check that action was sent. Note: The original message is also echoed back
        # because the 'continue' in the loop only continues the inner 'for part' loop, not the 'async for' loop.
        mock_websocket.send.assert_any_call(json.dumps(expected_action))

    async def test_pulse_monitor_starts(self):
        """Verify that boot_sequence starts the pulse_monitor task."""
        await self.orchestrator.boot_sequence()
        # Verify pulse_monitor task is in cleanup_tasks using its assigned name
        pulse_tasks = [t for t in self.orchestrator._cleanup_tasks if t.get_name() == "pulse_monitor"]
        self.assertTrue(len(pulse_tasks) > 0, "pulse_monitor task not found in _cleanup_tasks")

    async def test_pulse_monitor_cancellation(self):
        """Verify that shutdown cancels the pulse_monitor task."""
        await self.orchestrator.boot_sequence()
        pulse_tasks = [t for t in self.orchestrator._cleanup_tasks if t.get_name() == "pulse_monitor"]
        task = pulse_tasks[0]

        self.assertFalse(task.done())

        await self.orchestrator.shutdown()
        self.assertTrue(task.done() or task.cancelled())

    async def test_pulse_monitor_execution(self):
        """Verify that pulse_monitor executes its sleep loop."""
        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            # Use a side effect to raise CancelledError after one call to break the loop
            mock_sleep.side_effect = [None, asyncio.CancelledError()]

            try:
                await self.orchestrator.pulse_monitor(interval=0.001)
            except asyncio.CancelledError:
                pass

            self.assertTrue(mock_sleep.called)
            mock_sleep.assert_called_with(0.001)
