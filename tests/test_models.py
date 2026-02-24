import pytest
from dataclasses import asdict
from datetime import datetime
from agent.aether_forge.models import VoiceFeatures, ForgeResult, ScreenContext, CognitiveSystem

def test_voice_features_creation():
    features = VoiceFeatures(
        speech_rate_wpm=150.0,
        pitch_variance=0.5,
        volume_db=-10.0,
        pause_frequency=5.0,
        transcript="Hello world"
    )
    assert features.speech_rate_wpm == 150.0
    assert features.language == "ar"  # Default
    assert isinstance(features.timestamp, datetime)

    # Check urgency score calculation
    score = features.urgency_score
    assert 0.0 <= score <= 1.0

def test_forge_result_serialization():
    # Since ForgeResult doesn't have to_dict/from_dict, we test asdict
    result = ForgeResult(
        success=True,
        service="test_service",
        agent_id="agent_123",
        execution_ms=100.0,
        dna_crystallized=False,
        cognitive_system=CognitiveSystem.SYSTEM_1,
        data={"key": "value"}
    )

    data = asdict(result)
    assert data["success"] is True
    assert data["service"] == "test_service"
    assert data["data"] == {"key": "value"}
    # Enum serialization depends on how asdict handles it (usually returns the Enum object)
    assert data["cognitive_system"] == CognitiveSystem.SYSTEM_1

def test_screen_context_defaults():
    context = ScreenContext(
        raw_description="A screen",
        detected_assets=[],
        detected_app="Finder",
        detected_numbers=[]
    )

    assert context.screenshot_b64 is None
    assert context.confidence == 0.0
    assert isinstance(context.timestamp, datetime)
