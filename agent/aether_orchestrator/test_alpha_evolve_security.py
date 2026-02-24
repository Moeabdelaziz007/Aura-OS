
import unittest
import sys
import os
import importlib
from unittest.mock import MagicMock, patch

# Add current directory to path
sys.path.insert(0, os.getcwd())

class TestAlphaEvolveSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Setup mocks
        cls.mock_google = MagicMock()
        cls.mock_genai = MagicMock()
        cls.mock_dotenv = MagicMock()

        # Patch sys.modules
        cls.modules_patcher = patch.dict(sys.modules, {
            "google": cls.mock_google,
            "google.generativeai": cls.mock_genai,
            "dotenv": cls.mock_dotenv
        })
        cls.modules_patcher.start()

        # Reload modules
        import agent.aether_orchestrator.alpha_evolve
        importlib.reload(agent.aether_orchestrator.alpha_evolve)

        from agent.aether_orchestrator.alpha_evolve import MutationGenerator
        cls.MutationGenerator = MutationGenerator

    @classmethod
    def tearDownClass(cls):
        cls.modules_patcher.stop()

    def test_secret_redaction(self):
        """Test secret redaction in MutationGenerator (alpha_evolve)."""
        print("\n🧪 Testing Secret Redaction in alpha_evolve...")

        generator = self.MutationGenerator(use_gemini=False)

        # nosec - Testing redaction of fake secrets
        secret_code = """
    def connect():
        api_key = "sk-1234567890abcdef"
        password = 'SuperSecretPassword'
        token: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        regular_var = "not_a_secret"
        short_secret = "pass"
        secret_with_spaces   =   "spaced_secret"
    """ # nosec

        # Test Redaction
        redacted, secret_map = generator._redact_secrets(secret_code)

        self.assertNotIn("sk-1234567890abcdef", redacted)
        self.assertNotIn("SuperSecretPassword", redacted)
        self.assertNotIn("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9", redacted) # Should be redacted now
        self.assertNotIn("spaced_secret", redacted)

        self.assertIn("not_a_secret", redacted)
        self.assertNotIn('short_secret = "pass"', redacted) # Should be redacted (len >= 4)

        self.assertIn('token: str = "', redacted) # Check type hint structure preserved
        self.assertIn('secret_with_spaces   =   "', redacted) # Check spacing preserved

        self.assertEqual(len(secret_map), 5)
        self.assertTrue(any("sk-1234567890abcdef" == v for v in secret_map.values()))

        # Test Restoration
        restored = generator._restore_secrets(redacted, secret_map)
        self.assertEqual(restored, secret_code)

        print("✅ Secret Redaction tests passed (alpha_evolve)")

if __name__ == "__main__":
    unittest.main()
