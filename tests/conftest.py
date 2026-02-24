"""
Shared fixtures and configuration for AetherOS tests.

This module provides common pytest fixtures used across all test modules.
"""

import pytest
import asyncio
import json
import sys
import types
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from datetime import datetime
from pathlib import Path

# Mock heavy dependencies before imports
# Use ModuleType for google to allow submodule mocking
sys.modules["google"] = types.ModuleType("google")
sys.modules["google.genai"] = MagicMock()
sys.modules["google.generativeai"] = MagicMock()
sys.modules["google.cloud"] = MagicMock()
sys.modules["google.cloud.firestore"] = MagicMock()
sys.modules["firebase_admin"] = MagicMock()
sys.modules["firebase_admin.credentials"] = MagicMock()
sys.modules["firebase_admin.firestore"] = MagicMock()


# =============================================================================
# Async Event Loop Fixture
# =============================================================================

@pytest.fixture
def event_loop():
    """
    Create an instance of the default event loop for each test case.
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Mock DNA Response
# =============================================================================

@pytest.fixture
def mock_dna():
    """Mock DNA object with version information."""
    dna = Mock()
    dna.version = "v2.0.0"
    return dna


# =============================================================================
# Mock Bridge (AetherNavigator)
# =============================================================================

@pytest.fixture
def mock_bridge(mock_dna):
    """Mock AetherNavigator bridge instance."""
    bridge = Mock()
    bridge.load_dna_async = AsyncMock(return_value=mock_dna)
    bridge.close = AsyncMock()
    return bridge


# =============================================================================
# Mock Forge (AetherForge)
# =============================================================================

@pytest.fixture
def mock_forge():
    """Mock AetherForge instance."""
    forge = Mock()
    forge.__aenter__ = AsyncMock(return_value=forge)
    forge.__aexit__ = AsyncMock()
    forge.resolve_and_forge = AsyncMock()
    return forge


# =============================================================================
# Mock Router (HyperMindRouter)
# =============================================================================

@pytest.fixture
def mock_router():
    """Mock HyperMindRouter instance."""
    router = Mock()
    router.route_action = AsyncMock(return_value="AETHER_FORGE")
    return router


# =============================================================================
# Mock Memory Signal
# =============================================================================

@pytest.fixture
def mock_memory_signal():
    """Mock MemorySignal instance."""
    from agent.aether_forge.constraint_solver import MemorySignal
    return MemorySignal(
        recent_services=[],
        recent_assets=[],
        last_action=None,
        query_count_1h=0
    )


# =============================================================================
# Mock Forge Result
# =============================================================================

@pytest.fixture
def mock_forge_result():
    """Mock ForgeResult instance."""
    from agent.aether_forge.models import ForgeResult, CognitiveSystem
    return ForgeResult(
        success=True,
        service="coingecko",
        agent_id="test-agent-001",
        execution_ms=150.0,
        dna_crystallized=False,
        cognitive_system=CognitiveSystem.SYSTEM_1,
        data={"BTC": {"price": 50000, "change": 2.5}},
        ascii_visual="BTC: $50,000 (+2.5%)",
        error=None
    )


# =============================================================================
# Mock Gemini Live Client
# =============================================================================

@pytest.fixture
def mock_gemini_client():
    """Mock GeminiLiveClient instance."""
    client = Mock()
    client.connect = AsyncMock()
    client.close = AsyncMock()
    client.send_text = AsyncMock()
    client.stream_input = AsyncMock()
    client.listen = AsyncMock()
    return client


# =============================================================================
# Mock WebSocket
# =============================================================================

@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection."""
    ws = Mock()
    ws.remote_address = ("127.0.0.1", 8080)
    ws.open = True
    ws.send = AsyncMock()
    ws.__aiter__ = AsyncMock(return_value=iter([]))
    return ws


# =============================================================================
# Mock Voice Features
# =============================================================================

@pytest.fixture
def mock_voice_features():
    """Mock VoiceFeatures instance."""
    from agent.aether_forge.models import VoiceFeatures
    return VoiceFeatures(
        speech_rate_wpm=150.0,
        pitch_variance=0.5,
        volume_db=60.0,
        pause_frequency=10.0,
        transcript="check bitcoin price",
        language="en"
    )


# =============================================================================
# Mock Screen Context
# =============================================================================

@pytest.fixture
def mock_screen_context():
    """Mock ScreenContext instance."""
    from agent.aether_forge.models import ScreenContext
    return ScreenContext(
        raw_description="Binance trading interface showing BTC price",
        detected_assets=["BTC", "SOL"],
        detected_app="Binance",
        detected_numbers=[50000.0, 2500.0],
        confidence=0.9
    )


# =============================================================================
# Mock Time Context
# =============================================================================

@pytest.fixture
def mock_time_context():
    """Mock TimeContext instance."""
    from agent.aether_forge.models import TimeContext
    return TimeContext(
        hour=14,
        is_market_hours=True,
        day_of_week=1,
        is_weekend=False,
        market_session="open"
    )


# =============================================================================
# Mock Anomaly Monitor
# =============================================================================

@pytest.fixture
def mock_anomaly_monitor():
    """Mock NeuralMonitor instance."""
    monitor = Mock()
    monitor.anomaly_log = []
    monitor.log_anomaly = Mock()
    return monitor


# =============================================================================
# Mock Synaptic Message
# =============================================================================

@pytest.fixture
def mock_synaptic_message():
    """Mock SynapticMessage instance."""
    from agent.aether_forge.models import SynapticMessage
    return SynapticMessage(
        intent_text="check bitcoin price",
        data={"poison": None}
    )


# =============================================================================
# Temporary Directory for File Tests
# =============================================================================

@pytest.fixture
def temp_dir(tmp_path):
    """
    Create a temporary directory for file-based tests.
    Automatically cleaned up after the test.
    """
    return tmp_path


# =============================================================================
# Mock JSON File Content
# =============================================================================

@pytest.fixture
def mock_calibration_json():
    """Mock calibration JSON content."""
    return {
        "price_check": {"weight": 1.2},
        "github_search": {"weight": 1.0},
        "weather_check": {"weight": 0.8}
    }


# =============================================================================
# Callback Mocks
# =============================================================================

@pytest.fixture
def mock_update_memory_callback():
    """Mock update memory callback."""
    return Mock()


@pytest.fixture
def mock_log_anomaly_callback():
    """Mock log anomaly callback."""
    return Mock()


@pytest.fixture
def mock_trigger_healing_callback():
    """Mock trigger healing callback."""
    return AsyncMock()


# =============================================================================
# Mock API Key
# =============================================================================

@pytest.fixture
def mock_api_key():
    """Mock API key for Gemini Live."""
    return "test-api-key-1234567890"
