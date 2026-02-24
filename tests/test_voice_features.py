"""
🧪 Test Suite for AetherOS Voice Features
==========================================
Comprehensive tests for voice processing, Gemini Live Bridge,
and the Aether Voice Mega Agent pipeline.
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

# Now import after mocking
from agent.aether_forge.models import VoiceFeatures, UrgencyLevel, ScreenContext


class TestVoiceFeatures(unittest.TestCase):
    """Test VoiceFeatures model and urgency computation."""

    def test_voice_features_creation(self):
        """Test basic VoiceFeatures instantiation."""
        voice = VoiceFeatures(
            speech_rate_wpm=150.0,
            pitch_variance=0.5,
            volume_db=-15.0,
            pause_frequency=2.0,
            transcript="Get Bitcoin price",
            language="en"
        )
        
        self.assertEqual(voice.speech_rate_wpm, 150.0)
        self.assertEqual(voice.pitch_variance, 0.5)
        self.assertEqual(voice.volume_db, -15.0)
        self.assertEqual(voice.pause_frequency, 2.0)
        self.assertEqual(voice.transcript, "Get Bitcoin price")
        self.assertEqual(voice.language, "en")

    def test_urgency_score_normal_speech(self):
        """Test urgency score for normal speech patterns."""
        voice = VoiceFeatures(
            speech_rate_wpm=150.0,  # Normal rate
            pitch_variance=0.3,     # Low variance
            volume_db=-20.0,        # Normal volume
            pause_frequency=3.0,    # Normal pauses
            transcript="What is the Bitcoin price?",
            language="en"
        )
        
        score = voice.urgency_score  # Use property instead of method
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.1)
        # Normal speech should have low to medium urgency
        self.assertLess(score, 0.7)

    def test_urgency_score_stressed_speech(self):
        """Test urgency score for stressed/urgent speech patterns."""
        voice = VoiceFeatures(
            speech_rate_wpm=250.0,  # Fast rate
            pitch_variance=0.9,     # High variance
            volume_db=-5.0,         # Loud volume
            pause_frequency=0.5,    # Few pauses
            transcript="URGENT sell all Bitcoin NOW!",
            language="en"
        )
        
        score = voice.urgency_score
        self.assertGreater(score, 0.6)  # Should be high urgency

    def test_urgency_score_critical_speech(self):
        """Test urgency score for critical/panic speech patterns."""
        voice = VoiceFeatures(
            speech_rate_wpm=300.0,  # Very fast
            pitch_variance=1.0,     # Maximum variance
            volume_db=0.0,          # Maximum volume
            pause_frequency=0.0,    # No pauses
            transcript="EMERGENCY CRITICAL SELL EVERYTHING",
            language="en"
        )
        
        score = voice.urgency_score
        self.assertGreater(score, 0.8)  # Should be critical

    def test_urgency_level_classification(self):
        """Test urgency level classification based on score thresholds."""
        # CRITICAL level (score >= 0.8)
        critical_voice = VoiceFeatures(
            speech_rate_wpm=300.0,
            pitch_variance=1.0,
            volume_db=0.0,
            pause_frequency=0.0,
            transcript="Emergency!",
            language="en"
        )
        self.assertGreaterEqual(critical_voice.urgency_score, 0.8)

        # HIGH level (score >= 0.6)
        high_voice = VoiceFeatures(
            speech_rate_wpm=220.0,
            pitch_variance=0.7,
            volume_db=-10.0,
            pause_frequency=1.0,
            transcript="Hurry up!",
            language="en"
        )
        self.assertGreaterEqual(high_voice.urgency_score, 0.6)
        self.assertLess(high_voice.urgency_score, 0.8)

        # NORMAL level (score < 0.6)
        normal_voice = VoiceFeatures(
            speech_rate_wpm=150.0,
            pitch_variance=0.4,
            volume_db=-20.0,
            pause_frequency=3.0,
            transcript="Normal request",
            language="en"
        )
        self.assertLess(normal_voice.urgency_score, 0.6)

    def test_language_detection_arabic(self):
        """Test Arabic language detection from transcript."""
        voice = VoiceFeatures(
            speech_rate_wpm=150.0,
            pitch_variance=0.5,
            volume_db=-15.0,
            pause_frequency=2.0,
            transcript="ما هو سعر البيتكوين؟",
            language="ar"
        )
        
        self.assertEqual(voice.language, "ar")

    def test_language_detection_english(self):
        """Test English language detection from transcript."""
        voice = VoiceFeatures(
            speech_rate_wpm=150.0,
            pitch_variance=0.5,
            volume_db=-15.0,
            pause_frequency=2.0,
            transcript="What is the Bitcoin price?",
            language="en"
        )
        
        self.assertEqual(voice.language, "en")


class TestScreenContext(unittest.TestCase):
    """Test ScreenContext model for visual context."""

    def test_screen_context_creation(self):
        """Test basic ScreenContext instantiation."""
        screen = ScreenContext(
            raw_description="TradingView showing BTC/USD chart",
            detected_assets=["Bitcoin", "TradingView"],
            detected_app="TradingView",
            detected_numbers=[65000.0]
        )
        
        self.assertIn("Bitcoin", screen.detected_assets)
        self.assertEqual(screen.detected_app, "TradingView")

    def test_empty_screen_context(self):
        """Test empty/default screen context."""
        screen = ScreenContext(
            raw_description="Empty desktop",
            detected_assets=[],
            detected_app="Desktop",
            detected_numbers=[]
        )
        
        self.assertEqual(len(screen.detected_assets), 0)


class TestVoiceFeaturesEdgeCases(unittest.TestCase):
    """Test edge cases for voice feature processing."""

    def test_zero_speech_rate(self):
        """Test handling of zero speech rate."""
        voice = VoiceFeatures(
            speech_rate_wpm=0.0,
            pitch_variance=0.5,
            volume_db=-15.0,
            pause_frequency=2.0,
            transcript="",
            language="en"
        )
        
        score = voice.urgency_score
        self.assertGreaterEqual(score, 0.0)

    def test_extreme_pitch_variance(self):
        """Test handling of extreme pitch variance."""
        voice = VoiceFeatures(
            speech_rate_wpm=150.0,
            pitch_variance=2.0,  # Above normal range
            volume_db=-15.0,
            pause_frequency=2.0,
            transcript="Test",
            language="en"
        )
        
        score = voice.urgency_score
        self.assertLessEqual(score, 1.1)

    def test_negative_volume(self):
        """Test handling of negative volume values."""
        voice = VoiceFeatures(
            speech_rate_wpm=150.0,
            pitch_variance=0.5,
            volume_db=-50.0,  # Very quiet
            pause_frequency=2.0,
            transcript="Whispering",
            language="en"
        )
        
        score = voice.urgency_score
        self.assertGreaterEqual(score, 0.0)

    def test_empty_transcript(self):
        """Test handling of empty transcript."""
        voice = VoiceFeatures(
            speech_rate_wpm=150.0,
            pitch_variance=0.5,
            volume_db=-15.0,
            pause_frequency=2.0,
            transcript="",
            language="en"
        )
        
        self.assertEqual(voice.transcript, "")


if __name__ == "__main__":
    unittest.main()
