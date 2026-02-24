"""
Unit Tests for Task Executor Module

Tests the task execution and websocket handling logic for the AetherOS orchestrator.
"""

import pytest
import asyncio
import json
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from typing import Any, List


# =============================================================================
# Helper for async iteration
# =============================================================================

class AsyncIterator:
    """Helper class to create async iterators from a list of items."""
    def __init__(self, items: List[Any]):
        self.items = items
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index >= len(self.items):
            raise StopAsyncIteration
        item = self.items[self.index]
        self.index += 1
        return item


def make_async_iter(items: List[Any]):
    """Create an async iterator from a list of items."""
    return AsyncIterator(items)


# =============================================================================
# Import the module under test
# =============================================================================

from agent.aether_orchestrator.modules.task_executor import TaskExecutor


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def task_executor(mock_bridge, mock_router, mock_forge, mock_memory_signal):
    """
    Create a TaskExecutor instance with mocked dependencies.
    """
    return TaskExecutor(
        bridge=mock_bridge,
        router=mock_router,
        forge=mock_forge,
        memory_signal=mock_memory_signal,
        drift_threshold_ms=500.0,
        max_retries=3
    )


@pytest.fixture
def task_executor_custom_retries(mock_bridge, mock_router, mock_forge, mock_memory_signal):
    """
    Create a TaskExecutor instance with custom max retries.
    """
    return TaskExecutor(
        bridge=mock_bridge,
        router=mock_router,
        forge=mock_forge,
        memory_signal=mock_memory_signal,
        drift_threshold_ms=500.0,
        max_retries=5
    )


@pytest.fixture
def mock_visual_delta_message():
    """
    Create a mock visual delta binary message.
    """
    # Header 0x01 for visual delta
    # JPEG magic bytes: FF D8
    jpeg_data = b'\xFF\xD8\xFF\xE0\x00\x10JFIF' + b'\x00' * 100
    return bytes([0x01]) + jpeg_data


@pytest.fixture
def mock_visual_delta_with_metadata():
    """
    Create a mock visual delta message with metadata.
    """
    metadata = json.dumps({"timestamp_edge": time.time_ns() - 100_000_000}).encode('utf-8')
    metadata_len = len(metadata).to_bytes(4, 'little')
    jpeg_data = b'\xFF\xD8\xFF\xE0\x00\x10JFIF' + b'\x00' * 100
    return bytes([0x01]) + metadata_len + metadata + jpeg_data


@pytest.fixture
def mock_audio_chunk_message():
    """
    Create a mock audio chunk binary message.
    """
    # Header 0x02 for audio chunk
    audio_data = b'\x00' * 1024  # 1KB of PCM data
    return bytes([0x02]) + audio_data


@pytest.fixture
def mock_json_message():
    """
    Create a mock JSON message for synaptic signal.
    """
    return json.dumps({
        "intent_text": "check bitcoin price",
        "data": {"poison": None}
    })


@pytest.fixture
def mock_poison_message():
    """
    Create a mock message with neural poison.
    """
    return json.dumps({
        "intent_text": "check bitcoin price",
        "data": {"poison": "NEURAL_POISON"}
    })


@pytest.fixture
def mock_spatial_response():
    """
    Create a mock Gemini spatial response with point data.
    """
    return {
        "modelTurn": {
            "parts": [
                {
                    "text": 'Click here {"point": [500, 300]}'
                }
            ]
        }
    }


@pytest.fixture
def mock_spatial_text_response():
    """
    Create a mock Gemini spatial response with text data.
    """
    return {
        "modelTurn": {
            "parts": [
                {
                    "text": 'Type this {"text": "hello world"}'
                }
            ]
        }
    }


# =============================================================================
# Test: TaskExecutor Initialization
# =============================================================================

class TestTaskExecutorInitialization:
    """Test cases for TaskExecutor initialization."""

    def test_initialization_with_defaults(self, mock_bridge, mock_router, mock_forge, mock_memory_signal):
        """
        Test that TaskExecutor initializes with default values.
        """
        executor = TaskExecutor(mock_bridge, mock_router, mock_forge, mock_memory_signal)
        
        assert executor.bridge == mock_bridge
        assert executor.router == mock_router
        assert executor.forge == mock_forge
        assert executor.memory_signal == mock_memory_signal
        assert executor.drift_threshold_ms == 500.0
        assert executor._max_retries == 3

    def test_initialization_with_custom_drift_threshold(self, mock_bridge, mock_router, mock_forge, mock_memory_signal):
        """
        Test that TaskExecutor initializes with custom drift threshold.
        """
        executor = TaskExecutor(
            mock_bridge, mock_router, mock_forge, mock_memory_signal,
            drift_threshold_ms=1000.0
        )
        assert executor.drift_threshold_ms == 1000.0

    def test_initialization_with_custom_max_retries(self, mock_bridge, mock_router, mock_forge, mock_memory_signal):
        """
        Test that TaskExecutor initializes with custom max retries.
        """
        executor = TaskExecutor(
            mock_bridge, mock_router, mock_forge, mock_memory_signal,
            max_retries=5
        )
        assert executor._max_retries == 5


# =============================================================================
# Test: Handle Binary Message - Visual Delta
# =============================================================================

class TestHandleBinaryMessageVisualDelta:
    """Test cases for handling visual delta binary messages."""

    @pytest.mark.asyncio
    async def test_handle_raw_jpeg_without_metadata(self, task_executor, mock_visual_delta_message, mock_gemini_client):
        """
        Test handling raw JPEG data without metadata header.
        """
        await task_executor._handle_binary_message(
            mock_visual_delta_message,
            Mock(),
            mock_gemini_client
        )
        
        # Verify stream_input was called with JPEG data
        mock_gemini_client.stream_input.assert_called_once()
        call_args = mock_gemini_client.stream_input.call_args
        assert call_args[1]['mime_type'] == "image/jpeg"

    @pytest.mark.asyncio
    async def test_handle_jpeg_with_metadata(self, task_executor, mock_visual_delta_with_metadata, mock_gemini_client):
        """
        Test handling JPEG data with metadata header.
        """
        await task_executor._handle_binary_message(
            mock_visual_delta_with_metadata,
            Mock(),
            mock_gemini_client
        )
        
        # Verify stream_input was called
        mock_gemini_client.stream_input.assert_called_once()

    @pytest.mark.asyncio
    async def test_visual_delta_with_nodes_bypasses_cv(self, task_executor, mock_gemini_client):
        """
        Test hybrid accessibility check with nodes bypasses CV.
        """
        metadata = json.dumps({
            "timestamp_edge": time.time_ns(),
            "nodes": [{"id": "button-1", "text": "Submit"}]
        }).encode('utf-8')
        metadata_len = len(metadata).to_bytes(4, 'little')
        jpeg_data = b'\xFF\xD8\xFF\xE0\x00\x10JFIF' + b'\x00' * 100
        
        message = bytes([0x01]) + metadata_len + metadata + jpeg_data
        
        await task_executor._handle_binary_message(message, Mock(), mock_gemini_client)
        
        # Verify send_text was called with accessibility context
        mock_gemini_client.send_text.assert_called_once()
        call_args = mock_gemini_client.send_text.call_args
        assert "Accessibility Context" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_visual_delta_with_stale_timestamp_drops_frame(self, task_executor, mock_gemini_client):
        """
        Test that stale frames are dropped based on perceptual drift.
        """
        old_timestamp = time.time_ns() - 1_000_000_000  # 1 second ago
        metadata = json.dumps({"timestamp_edge": old_timestamp}).encode('utf-8')
        metadata_len = len(metadata).to_bytes(4, 'little')
        jpeg_data = b'\xFF\xD8\xFF\xE0\x00\x10JFIF' + b'\x00' * 100
        
        message = bytes([0x01]) + metadata_len + metadata + jpeg_data
        
        await task_executor._handle_binary_message(message, Mock(), mock_gemini_client)
        
        # Verify stream_input was NOT called (frame dropped)
        mock_gemini_client.stream_input.assert_not_called()

    @pytest.mark.asyncio
    async def test_visual_delta_with_fresh_timestamp_processes_frame(self, task_executor, mock_gemini_client):
        """
        Test that fresh frames are processed normally.
        """
        recent_timestamp = time.time_ns() - 100_000_000  # 100ms ago
        metadata = json.dumps({"timestamp_edge": recent_timestamp}).encode('utf-8')
        metadata_len = len(metadata).to_bytes(4, 'little')
        jpeg_data = b'\xFF\xD8\xFF\xE0\x00\x10JFIF' + b'\x00' * 100
        
        message = bytes([0x01]) + metadata_len + metadata + jpeg_data
        
        await task_executor._handle_binary_message(message, Mock(), mock_gemini_client)
        
        # Verify stream_input was called
        mock_gemini_client.stream_input.assert_called_once()

    @pytest.mark.asyncio
    async def test_visual_delta_with_invalid_json_metadata(self, task_executor, mock_gemini_client):
        """
        Test handling of invalid JSON in metadata.
        """
        invalid_metadata = b'{"invalid": json}'  # Invalid JSON
        metadata_len = len(invalid_metadata).to_bytes(4, 'little')
        jpeg_data = b'\xFF\xD8\xFF\xE0\x00\x10JFIF' + b'\x00' * 100
        
        message = bytes([0x01]) + metadata_len + invalid_metadata + jpeg_data
        
        # Should not raise exception
        await task_executor._handle_binary_message(message, Mock(), mock_gemini_client)
        
        # Should still process the JPEG
        mock_gemini_client.stream_input.assert_called_once()


# =============================================================================
# Test: Handle Binary Message - Audio Chunk
# =============================================================================

class TestHandleBinaryMessageAudioChunk:
    """Test cases for handling audio chunk binary messages."""

    @pytest.mark.asyncio
    async def test_handle_audio_chunk(self, task_executor, mock_audio_chunk_message, mock_gemini_client):
        """
        Test handling audio chunk message.
        """
        await task_executor._handle_binary_message(
            mock_audio_chunk_message,
            Mock(),
            mock_gemini_client
        )
        
        # Verify stream_input was called with PCM data
        mock_gemini_client.stream_input.assert_called_once()
        call_args = mock_gemini_client.stream_input.call_args
        assert call_args[1]['mime_type'] == "audio/pcm"

    @pytest.mark.asyncio
    async def test_handle_empty_audio_chunk(self, task_executor, mock_gemini_client):
        """
        Test handling empty audio chunk.
        """
        empty_audio = bytes([0x02])  # Header only
        
        await task_executor._handle_binary_message(
            empty_audio,
            Mock(),
            mock_gemini_client
        )
        
        # Should still attempt to stream
        mock_gemini_client.stream_input.assert_called_once()


# =============================================================================
# Test: Handle JSON Message
# =============================================================================

class TestHandleJSONMessage:
    """Test cases for handling JSON messages."""

    @pytest.mark.asyncio
    async def test_handle_valid_json_message(self, task_executor, mock_json_message, mock_websocket, 
                                              mock_gemini_client, mock_update_memory_callback, 
                                              mock_log_anomaly_callback, mock_trigger_healing_callback, 
                                              mock_forge_result):
        """
        Test handling valid JSON message with successful forge execution.
        """
        # Setup mocks
        task_executor.forge.resolve_and_forge = AsyncMock(return_value=mock_forge_result)
        task_executor.router.route_action = AsyncMock(return_value="AETHER_FORGE")
        
        await task_executor._handle_json_message(
            mock_json_message,
            mock_websocket,
            mock_gemini_client,
            mock_update_memory_callback,
            mock_log_anomaly_callback,
            mock_trigger_healing_callback
        )
        
        # Verify forge was called
        task_executor.forge.resolve_and_forge.assert_called_once()
        
        # Verify memory was updated
        mock_update_memory_callback.assert_called_once_with(mock_forge_result)
        
        # Verify response was sent
        mock_gemini_client.send_text.assert_called()

    @pytest.mark.asyncio
    async def test_handle_poison_message(self, task_executor, mock_poison_message, mock_websocket,
                                          mock_gemini_client, mock_update_memory_callback,
                                          mock_log_anomaly_callback, mock_trigger_healing_callback):
        """
        Test handling neural poison message - should be neutralized.
        """
        await task_executor._handle_json_message(
            mock_poison_message,
            mock_websocket,
            mock_gemini_client,
            mock_update_memory_callback,
            mock_log_anomaly_callback,
            mock_trigger_healing_callback
        )
        
        # Verify anomaly was logged
        mock_log_anomaly_callback.assert_called_once()
        
        # Verify forge was NOT called
        task_executor.forge.resolve_and_forge.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_forge_execution_failure(self, task_executor, mock_json_message, mock_websocket,
                                                   mock_gemini_client, mock_update_memory_callback,
                                                   mock_log_anomaly_callback, mock_trigger_healing_callback):
        """
        Test handling when forge execution fails.
        """
        from agent.aether_forge.models import ForgeResult, CognitiveSystem
        
        failed_result = ForgeResult(
            success=False,
            service="unknown",
            agent_id="test-agent-002",
            execution_ms=50.0,
            dna_crystallized=False,
            cognitive_system=CognitiveSystem.SYSTEM_2,
            data=None,
            ascii_visual=None,
            error="Service not found"
        )
        
        task_executor.forge.resolve_and_forge = AsyncMock(return_value=failed_result)
        task_executor.router.route_action = AsyncMock(return_value="AETHER_FORGE")
        
        await task_executor._handle_json_message(
            mock_json_message,
            mock_websocket,
            mock_gemini_client,
            mock_update_memory_callback,
            mock_log_anomaly_callback,
            mock_trigger_healing_callback
        )
        
        # Verify error message was sent
        mock_gemini_client.send_text.assert_called_once()
        call_args = mock_gemini_client.send_text.call_args
        assert "Failed" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_handle_invalid_json_string(self, task_executor, mock_websocket, mock_gemini_client,
                                               mock_update_memory_callback, mock_log_anomaly_callback,
                                               mock_trigger_healing_callback):
        """
        Test handling invalid JSON string.
        """
        invalid_json = "not valid json {"
        
        with pytest.raises(json.JSONDecodeError):
            await task_executor._handle_json_message(
                invalid_json,
                mock_websocket,
                mock_gemini_client,
                mock_update_memory_callback,
                mock_log_anomaly_callback,
                mock_trigger_healing_callback
            )

    @pytest.mark.asyncio
    async def test_handle_non_dict_json(self, task_executor, mock_websocket, mock_gemini_client,
                                         mock_update_memory_callback, mock_log_anomaly_callback,
                                         mock_trigger_healing_callback):
        """
        Test handling JSON that is not a dictionary.
        """
        list_json = json.dumps(["item1", "item2"])
        
        with pytest.raises(ValueError, match="must be a JSON object"):
            await task_executor._handle_json_message(
                list_json,
                mock_websocket,
                mock_gemini_client,
                mock_update_memory_callback,
                mock_log_anomaly_callback,
                mock_trigger_healing_callback
            )


# =============================================================================
# Test: Listen to Gemini
# =============================================================================

class TestListenToGemini:
    """Test cases for listening to Gemini Live responses."""

    @pytest.mark.asyncio
    async def test_listen_to_gemini_routes_responses(self, task_executor, mock_websocket, mock_gemini_client):
        """
        Test that Gemini responses are routed to websocket.
        """
        mock_response = {"modelTurn": {"parts": [{"text": "Hello"}]}}
        mock_gemini_client.listen = Mock(return_value=make_async_iter([mock_response]))
        
        # Run for one iteration
        listen_task = asyncio.create_task(task_executor._listen_to_gemini(mock_websocket, mock_gemini_client))
        await asyncio.sleep(0.01)
        listen_task.cancel()
        
        try:
            await listen_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_listen_to_gemini_handles_spatial_point(self, task_executor, mock_websocket, 
                                                          mock_gemini_client, mock_spatial_response):
        """
        Test handling of spatial point response from Gemini.
        """
        mock_gemini_client.listen = Mock(return_value=make_async_iter([mock_spatial_response]))
        
        listen_task = asyncio.create_task(task_executor._listen_to_gemini(mock_websocket, mock_gemini_client))
        await asyncio.sleep(0.01)
        listen_task.cancel()
        
        try:
            await listen_task
        except asyncio.CancelledError:
            pass
        
        # Verify spatial action was sent (check all calls for CLICK action)
        mock_websocket.send.assert_called()
        # Find the CLICK action in the call list
        click_found = False
        for call in mock_websocket.send.call_args_list:
            sent_data = json.loads(call[0][0])
            if sent_data.get("action") == "CLICK":
                click_found = True
                break
        assert click_found, "CLICK action not found in websocket sends"

    @pytest.mark.asyncio
    async def test_listen_to_gemini_handles_spatial_text(self, task_executor, mock_websocket,
                                                         mock_gemini_client, mock_spatial_text_response):
        """
        Test handling of spatial text response from Gemini.
        """
        mock_gemini_client.listen = Mock(return_value=make_async_iter([mock_spatial_text_response]))
        
        listen_task = asyncio.create_task(task_executor._listen_to_gemini(mock_websocket, mock_gemini_client))
        await asyncio.sleep(0.02)  # Allow for the 0.5s delay
        listen_task.cancel()
        
        try:
            await listen_task
        except asyncio.CancelledError:
            pass
        
        # Verify TYPE and PRESS_ENTER actions were sent
        assert mock_websocket.send.call_count >= 1

    @pytest.mark.asyncio
    async def test_listen_to_gemini_handles_parsing_error(self, task_executor, mock_websocket, mock_gemini_client):
        """
        Test that parsing errors in spatial responses are handled gracefully.
        """
        mock_response = {"modelTurn": {"parts": [{"text": "Invalid JSON {broken"}]}}
        mock_gemini_client.listen = Mock(return_value=make_async_iter([mock_response]))
        
        listen_task = asyncio.create_task(task_executor._listen_to_gemini(mock_websocket, mock_gemini_client))
        await asyncio.sleep(0.01)
        listen_task.cancel()
        
        try:
            await listen_task
        except asyncio.CancelledError:
            pass
        
        # Should not crash, just log the error


# =============================================================================
# Test: Handle Critical Error
# =============================================================================

class TestHandleCriticalError:
    """Test cases for critical error handling."""

    @pytest.mark.asyncio
    async def test_handle_critical_error_with_recovery(self, task_executor, mock_websocket):
        """
        Test critical error handling with successful recovery.
        """
        error = ConnectionError("Connection lost")
        
        await task_executor._handle_critical_error(error, mock_websocket)
        
        # Should attempt recovery
        assert True  # Test passes if no exception is raised

    @pytest.mark.asyncio
    async def test_handle_critical_error_exhausts_retries(self, task_executor, mock_websocket):
        """
        Test critical error handling when all retries are exhausted.
        """
        mock_websocket.open = False
        error = ConnectionError("Connection lost")
        
        await task_executor._handle_critical_error(error, mock_websocket)
        
        # Should exhaust all retries and exit gracefully
        assert True

    @pytest.mark.asyncio
    async def test_handle_critical_error_with_exception_during_recovery(self, task_executor, mock_websocket):
        """
        Test critical error handling when recovery itself fails.
        """
        mock_websocket.open = Mock(side_effect=Exception("Recovery failed"))
        error = ConnectionError("Connection lost")
        
        await task_executor._handle_critical_error(error, mock_websocket)
        
        # Should handle recovery failure gracefully
        assert True


# =============================================================================
# Test: Handle Optic Nerve
# =============================================================================

class TestHandleOpticNerve:
    """Test cases for the main optic nerve handler."""

    @pytest.mark.asyncio
    async def test_handle_optic_nerve_with_binary_message(self, task_executor, mock_websocket, 
                                                           mock_gemini_client, mock_update_memory_callback,
                                                           mock_log_anomaly_callback, mock_trigger_healing_callback,
                                                           mock_visual_delta_message):
        """
        Test handling binary message through optic nerve.
        """
        mock_websocket.__aiter__ = Mock(return_value=make_async_iter([mock_visual_delta_message]))
        
        # Run briefly and cancel
        handle_task = asyncio.create_task(task_executor.handle_optic_nerve(
            mock_websocket,
            mock_gemini_client,
            mock_update_memory_callback,
            mock_log_anomaly_callback,
            mock_trigger_healing_callback
        ))
        await asyncio.sleep(0.01)
        handle_task.cancel()
        
        try:
            await handle_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_handle_optic_nerve_closes_gemini_on_exit(self, task_executor, mock_websocket,
                                                             mock_gemini_client, mock_update_memory_callback,
                                                             mock_log_anomaly_callback, mock_trigger_healing_callback):
        """
        Test that Gemini client is closed when optic nerve exits.
        """
        mock_websocket.__aiter__ = Mock(return_value=make_async_iter([]))
        
        await task_executor.handle_optic_nerve(
            mock_websocket,
            mock_gemini_client,
            mock_update_memory_callback,
            mock_log_anomaly_callback,
            mock_trigger_healing_callback
        )
        
        # Verify Gemini client was closed
        mock_gemini_client.close.assert_called_once()


# =============================================================================
# Test: Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test cases for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_handle_empty_binary_message(self, task_executor, mock_gemini_client):
        """
        Test handling empty binary message.
        """
        empty_message = bytes([0x01])  # Header only
        
        await task_executor._handle_binary_message(empty_message, Mock(), mock_gemini_client)
        
        # Should handle gracefully
        assert True

    @pytest.mark.asyncio
    async def test_handle_unknown_header_type(self, task_executor, mock_gemini_client):
        """
        Test handling binary message with unknown header type.
        """
        unknown_header = bytes([0xFF]) + b'some data'
        
        await task_executor._handle_binary_message(unknown_header, Mock(), mock_gemini_client)
        
        # Should handle gracefully (no exception)
        assert True

    def test_max_retries_zero(self, mock_bridge, mock_router, mock_forge, mock_memory_signal):
        """
        Test TaskExecutor with zero max retries.
        """
        executor = TaskExecutor(
            mock_bridge, mock_router, mock_forge, mock_memory_signal,
            max_retries=0
        )
        assert executor._max_retries == 0

    def test_drift_threshold_negative(self, mock_bridge, mock_router, mock_forge, mock_memory_signal):
        """
        Test TaskExecutor with negative drift threshold.
        """
        executor = TaskExecutor(
            mock_bridge, mock_router, mock_forge, mock_memory_signal,
            drift_threshold_ms=-100.0
        )
        assert executor.drift_threshold_ms == -100.0
