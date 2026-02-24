import unittest
import sys
from unittest.mock import MagicMock, patch
from pathlib import Path
import importlib

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class TestAetherEvolvePaths(unittest.TestCase):
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

        # Reload modules to pick up mocks
        import agent.aether_orchestrator.aether_evolve
        importlib.reload(agent.aether_orchestrator.aether_evolve)

        # Import the module under test
        from agent.aether_orchestrator.aether_evolve import AetherHeuristicSandbox, AetherDnaCommitter, PROJECT_ROOT

        cls.AetherHeuristicSandbox = AetherHeuristicSandbox
        cls.AetherDnaCommitter = AetherDnaCommitter
        cls.PROJECT_ROOT = PROJECT_ROOT

    @classmethod
    def tearDownClass(cls):
        cls.modules_patcher.stop()

    def test_project_root_detection(self):
        """Test that PROJECT_ROOT is correctly determined."""
        # Check if PROJECT_ROOT is an absolute path
        self.assertTrue(self.PROJECT_ROOT.is_absolute())

        # Check if it ends with the expected folder structure (likely contains 'agent')
        # Or better, check if 'agent' is in the path or listdir
        self.assertTrue((self.PROJECT_ROOT / "agent").exists(), "Project root should contain 'agent' directory")

    def test_heuristic_sandbox_default_path(self):
        """Test AetherHeuristicSandbox uses PROJECT_ROOT by default."""
        sandbox = self.AetherHeuristicSandbox()
        self.assertEqual(sandbox.workspace_root, str(self.PROJECT_ROOT))
        self.assertNotEqual(sandbox.workspace_root, "/Users/cryptojoker710/Desktop/AetherOS")

    def test_dna_committer_default_path(self):
        """Test AetherDnaCommitter uses PROJECT_ROOT by default."""
        committer = self.AetherDnaCommitter()
        self.assertEqual(committer.workspace_root, str(self.PROJECT_ROOT))
        self.assertNotEqual(committer.workspace_root, "/Users/cryptojoker710/Desktop/AetherOS")

    def test_custom_path(self):
        """Test passing a custom path works."""
        import tempfile
        import shutil

        # Create a temporary directory securely
        temp_dir = tempfile.mkdtemp()
        try:
            custom_path = str(Path(temp_dir) / "custom" / "path")

            sandbox = self.AetherHeuristicSandbox(workspace_root=custom_path)
            self.assertEqual(sandbox.workspace_root, custom_path)

            committer = self.AetherDnaCommitter(workspace_root=custom_path)
            self.assertEqual(committer.workspace_root, custom_path)
        finally:
            shutil.rmtree(temp_dir)

if __name__ == '__main__':
    unittest.main()
