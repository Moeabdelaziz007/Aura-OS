import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import sys

# Mock dependencies to avoid import errors from package initialization
sys.modules["firebase_admin"] = MagicMock()
sys.modules["firebase_admin.credentials"] = MagicMock()
sys.modules["firebase_admin.firestore"] = MagicMock()
sys.modules["google"] = MagicMock()
sys.modules["google.cloud"] = MagicMock()
sys.modules["google.generativeai"] = MagicMock()
sys.modules["agent.core.telemetry"] = MagicMock()

# Now we can import from agent.forge.models
# Note: agent.forge.__init__ imports a lot of things.
# We might need to mock more things if other submodules fail to import.
# But let's try.

from agent.forge.models import (
    VoiceFeatures,
    NanoAgent,
    DNAPattern,
    ForgeMetrics,
    ForgeResult,
    VerifiedResult,
    DataProof,
    CognitiveSystem,
    TelemetryManager
)

class TestVoiceFeatures(unittest.TestCase):
    def test_urgency_score_calculation(self):
        # Case 1: Max urgency (fast speech, high pitch var, loud, no pauses)
        features = VoiceFeatures(
            speech_rate_wpm=250.0,  # rate_score = 1.0
            pitch_variance=1.0,     # pitch_score = 1.0
            volume_db=20.0,         # volume_score = 1.0 ((20+20)/40)
            pause_frequency=0.0,    # pause_penalty = 1.0 (1 - 0/20)
            transcript="test"
        )
        # Expected: 1.0*0.4 + 1.0*0.35 + 1.0*0.15 + 1.0*0.1 = 1.0
        self.assertAlmostEqual(features.urgency_score, 1.0)

        # Case 2: Min urgency (slow speech, monotone, quiet, many pauses)
        features = VoiceFeatures(
            speech_rate_wpm=0.0,    # rate_score = 0.0
            pitch_variance=0.0,     # pitch_score = 0.0
            volume_db=-20.0,        # volume_score = 0.0 ((-20+20)/40)
            pause_frequency=20.0,   # pause_penalty = 0.0 (1 - 20/20)
            transcript="test"
        )
        # Expected: 0.0
        self.assertAlmostEqual(features.urgency_score, 0.0)

        # Case 3: Mixed values
        features = VoiceFeatures(
            speech_rate_wpm=125.0,  # rate_score = 0.5
            pitch_variance=0.5,     # pitch_score = 0.5
            volume_db=0.0,          # volume_score = 0.5 ((0+20)/40)
            pause_frequency=10.0,   # pause_penalty = 0.5 (1 - 10/20)
            transcript="test"
        )
        # Expected: 0.5*0.4 + 0.5*0.35 + 0.5*0.15 + 0.5*0.1 = 0.5
        self.assertAlmostEqual(features.urgency_score, 0.5)

    def test_urgency_score_clamping(self):
        # Test that values outside expected ranges are clamped correctly
        features = VoiceFeatures(
            speech_rate_wpm=300.0,  # Should clamp to 1.0
            pitch_variance=1.5,     # No clamping in logic
            volume_db=100.0,        # Should clamp to 1.0
            pause_frequency=-5.0,   # Should clamp to > 1.0?
            transcript="test"
        )

        # Let's verify the logic for pitch_variance and pause_frequency clamping.
        # pitch_variance is passed directly. If it's > 1.0, score can exceed 1.0?
        # Code: pitch_score = self.pitch_variance
        # pause_penalty = max(1.0 - ... , 0.0)

        # Volume too low
        features_low_vol = VoiceFeatures(
            speech_rate_wpm=0, pitch_variance=0, volume_db=-100, pause_frequency=20, transcript="t"
        )
        # volume_score = min(max((-100+20)/40, 0.0), 1.0) = 0.0
        self.assertAlmostEqual(features_low_vol.urgency_score, 0.0)

        # Volume too high
        features_high_vol = VoiceFeatures(
            speech_rate_wpm=0, pitch_variance=0, volume_db=100, pause_frequency=20, transcript="t"
        )
        # volume_score = 1.0
        self.assertAlmostEqual(features_high_vol.urgency_score, 0.15) # 1.0 * 0.15

class TestNanoAgent(unittest.TestCase):
    def test_is_alive(self):
        # Fresh agent
        agent = NanoAgent(ttl_seconds=30)
        self.assertTrue(agent.is_alive)

        # Old agent
        old_time = datetime.utcnow() - timedelta(seconds=31)
        agent_expired = NanoAgent(created_at=old_time, ttl_seconds=30)
        self.assertFalse(agent_expired.is_alive)

    def test_age_ms(self):
        # Allow some small delta for execution time
        agent = NanoAgent()
        # Should be very close to 0
        self.assertLess(agent.age_ms, 1000)
        self.assertGreaterEqual(agent.age_ms, 0)

        # Manually set created_at
        past = datetime.utcnow() - timedelta(seconds=1)
        agent_1s = NanoAgent(created_at=past)
        # Should be around 1000ms
        self.assertAlmostEqual(agent_1s.age_ms, 1000, delta=100)

class TestDNAPattern(unittest.TestCase):
    def test_is_viable(self):
        # Viable
        pattern = DNAPattern(
            service="test", params_template={}, avg_latency_ms=100,
            success_rate=0.8, energy_credits=10.0
        )
        self.assertTrue(pattern.is_viable())

        # Not viable due to energy
        pattern_no_energy = DNAPattern(
            service="test", params_template={}, avg_latency_ms=100,
            success_rate=0.8, energy_credits=0.0
        )
        self.assertFalse(pattern_no_energy.is_viable())

        # Not viable due to success rate
        pattern_low_success = DNAPattern(
            service="test", params_template={}, avg_latency_ms=100,
            success_rate=0.1, energy_credits=10.0
        )
        self.assertFalse(pattern_low_success.is_viable())

class TestForgeMetrics(unittest.TestCase):
    def setUp(self):
        self.metrics = ForgeMetrics()

    def test_initial_state(self):
        self.assertEqual(self.metrics.total_requests, 0)
        self.assertEqual(self.metrics.successful, 0)
        self.assertEqual(self.metrics.failed, 0)
        self.assertEqual(self.metrics.success_rate, 0.0)
        self.assertEqual(self.metrics.avg_latency_ms, 0.0)

    @patch("agent.core.telemetry.TelemetryManager.update")
    def test_record_success(self, mock_telemetry_update):
        result = MagicMock(spec=ForgeResult)
        result.success = True
        result.execution_ms = 100.0
        result.cognitive_system = CognitiveSystem.SYSTEM_1 # Need to set this for telemetry

        with patch("asyncio.create_task") as mock_create_task:
            self.metrics.record(result)

            self.assertEqual(self.metrics.total_requests, 1)
            self.assertEqual(self.metrics.successful, 1)
            self.assertEqual(self.metrics.failed, 0)
            self.assertEqual(self.metrics.total_latency_ms, 100.0)
            self.assertEqual(self.metrics.success_rate, 1.0)
            self.assertEqual(self.metrics.avg_latency_ms, 100.0)

            # Verify telemetry update was scheduled
            mock_create_task.assert_called_once()

    @patch("agent.core.telemetry.TelemetryManager.update")
    def test_record_failure(self, mock_telemetry_update):
        result = MagicMock(spec=ForgeResult)
        result.success = False
        result.execution_ms = 50.0
        result.cognitive_system = CognitiveSystem.SYSTEM_2

        with patch("asyncio.create_task") as mock_create_task:
            self.metrics.record(result)

            self.assertEqual(self.metrics.total_requests, 1)
            self.assertEqual(self.metrics.successful, 0)
            self.assertEqual(self.metrics.failed, 1)
            self.assertEqual(self.metrics.success_rate, 0.0)

            mock_create_task.assert_called_once()

class TestForgeResult(unittest.TestCase):
    def test_display_success(self):
        result = ForgeResult(
            success=True,
            service="test_service",
            agent_id="agent123",
            execution_ms=123.45,
            dna_crystallized=True,
            cognitive_system=CognitiveSystem.SYSTEM_1,
            ascii_visual="[CHART]"
        )
        display_str = result.display()
        self.assertIn("✅ DISSOLVED", display_str)
        self.assertIn("test_service", display_str.lower())
        self.assertIn("123ms", display_str)
        self.assertIn("System 1", display_str)
        self.assertIn("Crystallized", display_str)
        self.assertIn("[CHART]", display_str)

    def test_display_failure_with_error(self):
        result = ForgeResult(
            success=False,
            service="fail_service",
            agent_id="agent456",
            execution_ms=50.0,
            dna_crystallized=False,
            cognitive_system=CognitiveSystem.SYSTEM_2,
            error="Something went wrong"
        )
        display_str = result.display()
        self.assertIn("❌ FAILED", display_str)
        self.assertIn("Something went wrong", display_str)
        self.assertIn("System 2", display_str)
        self.assertIn("Synthesized", display_str)

    def test_display_verified(self):
        proof1 = DataProof("src1", 100, {}, 10)
        proof2 = DataProof("src2", 100, {}, 10)
        verified = VerifiedResult(proof1, proof2, 100, 0.0, True)

        result = ForgeResult(
            success=True,
            service="verify_service",
            agent_id="agent789",
            execution_ms=10.0,
            dna_crystallized=True,
            cognitive_system=CognitiveSystem.SYSTEM_1,
            verified=verified
        )
        display_str = result.display()
        self.assertIn("✅ Trusted", display_str)
        self.assertIn("0.0% deviation", display_str)

if __name__ == "__main__":
    unittest.main()
