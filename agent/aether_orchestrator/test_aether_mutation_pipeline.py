"""
Test the AetherEvolve Mutation Pipeline
Tests the activation, generation, validation, and telemetry tracking of mutations.
"""

import asyncio
import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import importlib

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# We need to test functionality that depends on google.generativeai, but avoid polluting
# sys.modules globally for other tests in the suite.

class TestAetherMutationPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Setup mocks for dependencies
        cls.mock_google = MagicMock()
        cls.mock_genai = MagicMock()
        cls.mock_dotenv = MagicMock()

        # Mock telemetry module to avoid import errors during testing
        cls.mock_telemetry = MagicMock()

        # Patch sys.modules to inject mocks
        cls.modules_patcher = patch.dict(sys.modules, {
            "google": cls.mock_google,
            "google.generativeai": cls.mock_genai,
            "dotenv": cls.mock_dotenv,
            "agent.aether_core.aether_telemetry": cls.mock_telemetry
        })
        cls.modules_patcher.start()

        # Import the module under test AFTER patching
        # If it was already imported, reload it to pick up mocks
        import agent.aether_orchestrator.alpha_evolve
        import agent.aether_orchestrator.aether_evolve
        importlib.reload(agent.aether_orchestrator.alpha_evolve)
        importlib.reload(agent.aether_orchestrator.aether_evolve)

        from agent.aether_orchestrator.aether_evolve import (
            AetherEvolve,
            AetherNeuralMonitor,
            MutationGenerator,
            MutationValidator,
            MutationTracker,
            AnomalyAnalyzer,
            MUTATION_TEMPLATES,
            DANGEROUS_PATTERNS
        )

        cls.AetherEvolve = AetherEvolve
        cls.AetherNeuralMonitor = AetherNeuralMonitor
        cls.MutationGenerator = MutationGenerator
        cls.MutationValidator = MutationValidator
        cls.MutationTracker = MutationTracker
        cls.AnomalyAnalyzer = AnomalyAnalyzer
        cls.MUTATION_TEMPLATES = MUTATION_TEMPLATES
        cls.DANGEROUS_PATTERNS = DANGEROUS_PATTERNS

    @classmethod
    def tearDownClass(cls):
        # Stop patching sys.modules
        cls.modules_patcher.stop()

        # We should reload the modules again to restore original imports if possible,
        # or at least ensure they are re-imported correctly next time they are needed.
        # However, since these modules might not be importable in the test env without mocks,
        # we just let the patcher cleanup the mock entries from sys.modules.
        pass

    def test_mutation_tracker(self):
        """Test the MutationTracker class."""
        print("\n🧪 Testing MutationTracker...")

        tracker = self.MutationTracker()

        # Record some mutations
        tracker.record_mutation("ZeroDivisionError", "Orchestrator", True, "mut_001")
        tracker.record_mutation("FileNotFoundError", "Forge", False, "mut_002")
        tracker.record_mutation("ZeroDivisionError", "Orchestrator", True, "mut_003")

        metrics = tracker.get_metrics()

        self.assertEqual(metrics["total_mutations"], 3)
        self.assertEqual(metrics["successful_mutations"], 2)
        self.assertEqual(metrics["failed_mutations"], 1)
        self.assertEqual(metrics["mutations_by_type"]["ZeroDivisionError"], 2)
        self.assertEqual(metrics["mutations_by_component"]["Orchestrator"], 2)

        print("✅ MutationTracker tests passed")

    def test_mutation_validator(self):
        """Test the MutationValidator class."""
        print("\n🧪 Testing MutationValidator...")

        validator = self.MutationValidator()

        # Test safe mutation
        safe_code = "def foo():\n    return 42"
        is_safe, reason = validator.is_safe_mutation(safe_code, safe_code + "\n    pass")
        self.assertTrue(is_safe, f"Expected safe mutation, got: {reason}")

        # Test dangerous pattern - rm -rf
        dangerous_code = "import os\nos.system('rm -rf /')"
        is_safe, reason = validator.is_safe_mutation(safe_code, dangerous_code)
        self.assertFalse(is_safe, "Expected unsafe mutation for rm -rf")

        # Test dangerous pattern - eval
        eval_code = "eval('print(1)')"
        is_safe, reason = validator.is_safe_mutation(safe_code, eval_code)
        self.assertFalse(is_safe, "Expected unsafe mutation for eval")

        # Test empty mutation
        is_safe, reason = validator.is_safe_mutation(safe_code, "")
        self.assertFalse(is_safe, "Expected unsafe mutation for empty code")

        # Test syntax error
        syntax_error_code = "def foo(\n    # missing parenthesis"
        is_safe, reason = validator.is_safe_mutation(safe_code, syntax_error_code)
        self.assertFalse(is_safe, "Expected unsafe mutation for syntax error")

        # Test template validation
        self.assertTrue(validator.validate_mutation_template("ZeroDivisionError", "x = 1/0"))
        self.assertFalse(validator.validate_mutation_template("UnknownError", "x = 1/0"))

        print("✅ MutationValidator tests passed")

    def test_mutation_templates(self):
        """Test mutation templates exist for common error types."""
        print("\n🧪 Testing Mutation Templates...")

        expected_templates = [
            "ZeroDivisionError",
            "FileNotFoundError",
            "KeyError",
            "AttributeError",
            "TypeError",
            "IndexError",
            "ValueError",
            "ConnectionError",
            "TimeoutError"
        ]

        for template_name in expected_templates:
            self.assertIn(template_name, self.MUTATION_TEMPLATES)
            self.assertIn("description", self.MUTATION_TEMPLATES[template_name])
            self.assertIn("patterns", self.MUTATION_TEMPLATES[template_name])
            self.assertIn("fix_template", self.MUTATION_TEMPLATES[template_name])

        print(f"✅ All {len(expected_templates)} mutation templates present")

    def test_dangerous_patterns(self):
        """Test dangerous patterns are defined."""
        print("\n🧪 Testing Dangerous Patterns...")

        # Verify dangerous patterns list is not empty
        self.assertGreater(len(self.DANGEROUS_PATTERNS), 0)

        # Verify critical patterns are present
        critical_patterns = [
            "rm",      # File deletion
            "rmtree",  # Directory deletion
            "eval",    # Code execution
            "exec",    # Code execution
            "pickle"   # Deserialization
        ]

        for pattern in critical_patterns:
            found = any(pattern in dp for dp in self.DANGEROUS_PATTERNS)
            self.assertTrue(found, f"Missing dangerous pattern containing: {pattern}")

        print(f"✅ All {len(self.DANGEROUS_PATTERNS)} dangerous patterns defined")

    def test_anomaly_analyzer(self):
        """Test the AnomalyAnalyzer class."""
        print("\n🧪 Testing AnomalyAnalyzer...")

        # Create a temporary test anomaly log
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
            test_log_path = tmp.name

        test_anomalies = [
            {
                "timestamp": "2026-02-23T15:00:00",
                "component": "Orchestrator",
                "error_type": "ZeroDivisionError",
                "message": "division by zero",
                "status": "DETECTED"
            },
            {
                "timestamp": "2026-02-23T15:01:00",
                "component": "Orchestrator",
                "error_type": "ZeroDivisionError",
                "message": "division by zero",
                "status": "DETECTED"
            },
            {
                "timestamp": "2026-02-23T15:02:00",
                "component": "Forge",
                "error_type": "FileNotFoundError",
                "message": "file not found",
                "status": "DETECTED"
            },
            {
                "timestamp": "2026-02-23T15:03:00",
                "component": "Orchestrator",
                "error_type": "ZeroDivisionError",
                "message": "division by zero",
                "status": "HEALED"
            }
        ]

        with open(test_log_path, 'w') as f:
            json.dump(test_anomalies, f)

        try:
            analyzer = self.AnomalyAnalyzer(test_log_path)

            # Test loading
            anomalies = analyzer.load_anomalies()
            self.assertEqual(len(anomalies), 4)

            # Test grouping (should exclude HEALED status)
            grouped = analyzer.group_anomalies()
            # Only 2 groups: ZeroDivisionError_Orchestrator (2 DETECTED) and FileNotFoundError_Forge (1 DETECTED)
            self.assertEqual(len(grouped), 2)

            # Test prioritization
            prioritized = analyzer.prioritize_anomalies()
            self.assertEqual(len(prioritized), 2)
            # ZeroDivisionError should be first (higher frequency)
            self.assertIn("ZeroDivisionError", prioritized[0][0])

            print("✅ AnomalyAnalyzer tests passed")
        finally:
            # Clean up
            if os.path.exists(test_log_path):
                os.remove(test_log_path)

    def test_pipeline_activation(self):
        """Test pipeline activation and deactivation."""
        print("\n🧪 Testing Pipeline Activation...")

        monitor = self.AetherNeuralMonitor()
        evolve = self.AetherEvolve(monitor)

        # Test initial state
        self.assertFalse(evolve.is_pipeline_active)

        # Test activation
        status = evolve.activate_pipeline(max_mutations=3, rate_limit=5)
        self.assertEqual(status["status"], "activated")
        self.assertTrue(evolve.is_pipeline_active)
        self.assertEqual(evolve.max_mutations_per_cycle, 3)
        self.assertEqual(evolve.mutation_rate_limit, 5)

        # Test pipeline status
        pipeline_status = evolve.get_pipeline_status()
        self.assertTrue(pipeline_status["is_active"])
        self.assertIn("metrics", pipeline_status)

        # Test deactivation
        status = evolve.deactivate_pipeline()
        self.assertEqual(status["status"], "deactivated")
        self.assertFalse(evolve.is_pipeline_active)

        print("✅ Pipeline activation tests passed")

    async def async_test_template_mutation_generation(self):
        """Test template-based mutation generation."""
        print("\n🧪 Testing Template Mutation Generation...")

        generator = self.MutationGenerator(use_gemini=False)

        anomaly = {
            "component": "TestComponent",
            "error_type": "ZeroDivisionError",
            "message": "division by zero"
        }
        
        source_code = "def calculate():\n    return 10 / 0"
        
        mutation = await generator.generate_mutation(anomaly, source_code)
        
        self.assertIsNotNone(mutation)
        self.assertIn("AETHER_EVOLVE_FIX", mutation)
        self.assertIn("ZeroDivisionError", mutation)
        
        print("✅ Template mutation generation tests passed")

    def test_template_mutation_generation(self):
        asyncio.run(self.async_test_template_mutation_generation())

    async def async_test_telemetry_integration(self):
        """Test telemetry integration."""
        print("\n🧪 Testing Telemetry Integration...")

        monitor = self.AetherNeuralMonitor()
        evolve = self.AetherEvolve(monitor)

        # Activate pipeline
        evolve.activate_pipeline()

        # Record a mutation
        evolve.mutation_tracker.record_mutation("ZeroDivisionError", "Orchestrator", True, "test_mut_001")
        
        # Update telemetry
        # Ensure AetherTelemetryManager.aether_update is mocked on the mocked module
        mock_update = self.mock_telemetry.AetherTelemetryManager.aether_update
        mock_update.return_value = asyncio.Future()
        mock_update.return_value.set_result(None)

        await evolve._update_telemetry()

        # Check if called
        mock_update.assert_called_once()
        
        print("✅ Telemetry integration tests passed")

    def test_telemetry_integration(self):
        asyncio.run(self.async_test_telemetry_integration())

    def test_secret_redaction(self):
        """Test secret redaction in MutationGenerator."""
        print("\n🧪 Testing Secret Redaction...")

        generator = self.MutationGenerator(use_gemini=False)

        # nosec - Testing redaction of fake secrets
        secret_code = """
    def connect():
        api_key = "sk-1234567890abcdef"
        password = 'SuperSecretPassword'
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        regular_var = "not_a_secret"
        short_secret = "pass"
    """ # nosec

        # Test Redaction
        redacted, secret_map = generator._redact_secrets(secret_code)

        self.assertNotIn("sk-1234567890abcdef", redacted)
        self.assertNotIn("SuperSecretPassword", redacted)
        self.assertNotIn("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9", redacted)
        self.assertIn("not_a_secret", redacted)
        self.assertNotIn('short_secret = "pass"', redacted) # Should redact short strings (len >= 4)

        self.assertEqual(len(secret_map), 4)
        self.assertTrue(any("sk-1234567890abcdef" == v for v in secret_map.values()))

        # Test Restoration
        restored = generator._restore_secrets(redacted, secret_map)
        self.assertEqual(restored, secret_code)

        print("✅ Secret Redaction tests passed")

if __name__ == "__main__":
    unittest.main()
