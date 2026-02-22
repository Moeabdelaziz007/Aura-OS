
import unittest
from unittest.mock import MagicMock, patch
import asyncio
from agent.orchestrator.cognitive_router import HyperMindRouter
from agent.orchestrator.memory_parser import DNABelief, AuraNavigator

class TestCognitiveRouter(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Create a mock for AuraNavigator
        self.mock_bridge = MagicMock(spec=AuraNavigator)
        self.router = HyperMindRouter(self.mock_bridge)

        # Create a dummy DNA object
        self.dna_inference = {}
        self.dna_soul = {"defaults": {}}

        # We need a DNABelief object. Since it's a dataclass, we can instantiate it or mock it.
        # It's safer to instantiate it if possible to behave like the real object,
        # but we can also use a MagicMock that has the required attributes.
        # Given DNABelief is a simple dataclass, let's use a MagicMock to be flexible
        # and avoid needing to fill all fields.
        self.mock_dna = MagicMock(spec=DNABelief)
        self.mock_dna.inference = self.dna_inference
        self.mock_dna.soul = self.dna_soul

        # Setup load_dna_async to return our mock DNA
        async def load_dna_async(force=False):
            return self.mock_dna
        self.mock_bridge.load_dna_async.side_effect = load_dna_async

    async def test_update_cognitive_weights_cooldown(self):
        """Test that weights are not updated if the cooldown period hasn't passed."""
        # Setup: Last update was recent
        current_time = 1000.0
        self.dna_inference["cognitive_last_update"] = current_time - 30.0 # 30 seconds ago

        with patch("agent.orchestrator.cognitive_router.asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.time.return_value = current_time

            # Action: Try to update weights
            await self.router.update_cognitive_weights(feedback=1.0)

            # Assert: No changes should have happened
            # Specifically, cognitive_last_update should not have been updated to current_time
            self.assertEqual(self.dna_inference["cognitive_last_update"], current_time - 30.0)

    async def test_update_cognitive_weights_initialization(self):
        """Test that weights and baselines are initialized if missing."""
        current_time = 1000.0
        # Setup: No weights or baselines in inference
        self.dna_inference.clear()

        with patch("agent.orchestrator.cognitive_router.asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.time.return_value = current_time

            # Action: Update weights (feedback 0 to isolate initialization)
            await self.router.update_cognitive_weights(feedback=0.0)

            # Assert: Weights and baselines should be initialized
            self.assertIn("cognitive_weights", self.dna_inference)
            self.assertIn("cognitive_baselines", self.dna_inference)

            weights = self.dna_inference["cognitive_weights"]
            baselines = self.dna_inference["cognitive_baselines"]

            # Check default values
            self.assertEqual(weights["epistemic_curiosity (info)"], 0.5)
            self.assertEqual(weights["pragmatic_utility (pref)"], 0.5)
            self.assertEqual(weights["surprise_threshold (tau)"], 0.15)

            # Baselines should match weights initially
            self.assertEqual(baselines["epistemic_curiosity (info)"], 0.5)
            self.assertEqual(baselines["pragmatic_utility (pref)"], 0.5)

    async def test_update_cognitive_weights_positive_feedback(self):
        """Test that weights increase with positive feedback."""
        current_time = 1000.0
        self.dna_inference["cognitive_last_update"] = 0

        # Initialize weights
        weights = {
            "epistemic_curiosity (info)": 0.5,
            "pragmatic_utility (pref)": 0.5,
            "surprise_threshold (tau)": 0.15
        }
        baselines = weights.copy()
        self.dna_inference["cognitive_weights"] = weights
        self.dna_inference["cognitive_baselines"] = baselines

        with patch("agent.orchestrator.cognitive_router.asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.time.return_value = current_time

            # Action: Update with positive feedback
            # lr default is 0.01. Feedback 1.0 -> increase by 0.01
            await self.router.update_cognitive_weights(feedback=1.0)

            # Assert: Weights increased
            # 0.5 + 0.01 * 1.0 = 0.51. Clamping limit is 0.1 * 0.5 = 0.05. 0.01 is within limit.
            self.assertAlmostEqual(weights["epistemic_curiosity (info)"], 0.51)
            self.assertAlmostEqual(weights["pragmatic_utility (pref)"], 0.51)

            # Complexity bias decreases with positive feedback
            # Default bias is 0.05. New bias = 0.05 + 0.01 * (-1.0) = 0.04
            self.assertAlmostEqual(self.dna_inference["complexity_bias"], 0.04)

    async def test_update_cognitive_weights_clamping(self):
        """Test that weight updates are clamped to 10% of baseline."""
        current_time = 1000.0
        self.dna_inference["cognitive_last_update"] = 0

        # Initialize weights
        weights = {
            "epistemic_curiosity (info)": 0.5,
            "pragmatic_utility (pref)": 0.5,
            "surprise_threshold (tau)": 0.15
        }
        baselines = weights.copy()
        self.dna_inference["cognitive_weights"] = weights
        self.dna_inference["cognitive_baselines"] = baselines

        with patch("agent.orchestrator.cognitive_router.asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.time.return_value = current_time

            # Action: Large positive feedback
            # Try to increase by 0.1 (feedback 10.0, lr 0.01)
            # Max delta allowed is 0.1 * 0.5 = 0.05
            # Expected result: 0.5 + 0.05 = 0.55
            await self.router.update_cognitive_weights(feedback=10.0)

            # Assert: Clamped to baseline + 10%
            self.assertAlmostEqual(weights["epistemic_curiosity (info)"], 0.55)

            # Reset and try large negative feedback
            self.dna_inference["cognitive_last_update"] = 0 # reset cooldown check
            weights["epistemic_curiosity (info)"] = 0.5 # reset weight

            # Try to decrease by 0.1
            # Expected result: 0.5 - 0.05 = 0.45
            await self.router.update_cognitive_weights(feedback=-10.0)

            self.assertAlmostEqual(weights["epistemic_curiosity (info)"], 0.45)

    async def test_update_cognitive_weights_bounds(self):
        """Test that weights stay within [0, 1]."""
        current_time = 1000.0
        self.dna_inference["cognitive_last_update"] = 0

        # Initialize weights near boundary
        weights = {
            "epistemic_curiosity (info)": 0.01,
            "pragmatic_utility (pref)": 0.99,
            "surprise_threshold (tau)": 0.15
        }
        # Set baselines such that clamping doesn't prevent hitting 0 or 1
        # If baseline is 0.5, max delta is 0.05. Range [0.45, 0.55].
        # We need baselines that allow reaching 0 and 1 or check if clamping logic overrides bounds logic.
        # The code:
        # 1. Calculate updated = current + lr * feedback
        # 2. Clamp delta to ±10% of BASELINE.
        # 3. Clamp result to [0, 1].

        # So if baseline is 0.5, we can never reach 0 or 1 because we are stuck in [0.45, 0.55].
        # To test [0,1] bounds, we need a baseline that allows it, or check that [0,1] clamp is applied.
        # Let's use a scenario where baseline allows movement but 0/1 limit is hit first.
        # Example: Baseline = 0.1. Max delta = 0.01. Range [0.09, 0.11]. Still tight.

        # Wait, if `updated` is clamped by baseline logic, it might not reach 0 or 1 unless baseline is close to edges.
        # Let's set baseline to 0.0 and 1.0 (though unusual).
        baselines = {
             "epistemic_curiosity (info)": 0.0,
             "pragmatic_utility (pref)": 1.0,
             "surprise_threshold (tau)": 0.15
        }
        self.dna_inference["cognitive_weights"] = weights
        self.dna_inference["cognitive_baselines"] = baselines

        with patch("agent.orchestrator.cognitive_router.asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.time.return_value = current_time

            # Case 1: Try to go below 0
            # Current 0.01. Baseline 0.0. Max delta 0.0.
            # If baseline is 0, max_delta is 0. So updated = current.
            # This logic prevents movement if baseline is 0.

            # Let's try a different approach. The code has:
            # weights[key] = min(max(updated, 0), 1)
            # This is the final step.

            # If I want to verify this line, I need `updated` to be outside [0, 1] AFTER baseline clamping.
            # Suppose current=0.9, baseline=0.9. Max delta=0.09. Range [0.81, 0.99].
            # Suppose current=0.95, baseline=0.9. Max delta=0.09. Range [0.81, 0.99].
            # It seems the baseline clamping is very restrictive (10% of baseline).
            # This effectively keeps the value within ±10% of the initial value permanently,
            # unless the baseline itself changes (which it doesn't seem to in this function).

            # So the [0,1] clamp is almost redundant unless baseline is very large (e.g. > 10) or small?
            # If baseline is 0.5, range is [0.45, 0.55]. 0 and 1 are far away.
            # If baseline is 1.0, range is [0.9, 1.1]. Here upper bound 1.1 > 1.0.
            # So if baseline is 1.0, we can test the upper bound 1.0.

            # Reset
            weights["epistemic_curiosity (info)"] = 1.0
            baselines["epistemic_curiosity (info)"] = 1.0

            # Try to increase
            # Feedback 10.0 -> +0.1.
            # Max delta = 0.1 * 1.0 = 0.1.
            # Updated = 1.0 + 0.1 = 1.1.
            # Should be clamped to 1.0.
            await self.router.update_cognitive_weights(feedback=10.0)
            self.assertEqual(weights["epistemic_curiosity (info)"], 1.0)

            # Test complexity bias bounds (it doesn't use baseline clamping)
            # bias += lr * (-feedback)
            # bias default 0.05.
            # Feedback -100. bias += 0.01 * 100 = 1.0. New bias 1.05. Clamped to 1.0.
            self.dna_inference["cognitive_last_update"] = 0 # reset cooldown
            self.dna_inference["complexity_bias"] = 0.05
            await self.router.update_cognitive_weights(feedback=-100.0)
            self.assertEqual(self.dna_inference["complexity_bias"], 1.0)

            # Feedback 100. bias += 0.01 * (-100) = -1.0. New bias -0.95. Clamped to 0.0.
            self.dna_inference["cognitive_last_update"] = 0 # reset cooldown
            self.dna_inference["complexity_bias"] = 0.05
            await self.router.update_cognitive_weights(feedback=100.0)
            self.assertEqual(self.dna_inference["complexity_bias"], 0.0)

if __name__ == "__main__":
    unittest.main()
