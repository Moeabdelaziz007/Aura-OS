import sys
from unittest.mock import MagicMock

# Mock dependencies
sys.modules["google"] = MagicMock()
sys.modules["google.generativeai"] = MagicMock()
sys.modules["dotenv"] = MagicMock()

import unittest
from pathlib import Path
# Now import the module under test
from agent.aether_orchestrator.aether_evolve import AetherHeuristicSandbox, AetherDnaCommitter, PROJECT_ROOT

class TestAetherEvolvePaths(unittest.TestCase):
    def test_project_root_detection(self):
        """Test that PROJECT_ROOT is correctly determined."""
        # Check if PROJECT_ROOT is an absolute path
        self.assertTrue(PROJECT_ROOT.is_absolute())

        # Check if it ends with the expected folder structure (likely contains 'agent')
        # Or better, check if 'agent' is in the path or listdir
        self.assertTrue((PROJECT_ROOT / "agent").exists(), "Project root should contain 'agent' directory")

    def test_heuristic_sandbox_default_path(self):
        """Test AetherHeuristicSandbox uses PROJECT_ROOT by default."""
        sandbox = AetherHeuristicSandbox()
        self.assertEqual(sandbox.workspace_root, str(PROJECT_ROOT))
        self.assertNotEqual(sandbox.workspace_root, "/Users/cryptojoker710/Desktop/AetherOS")

    def test_dna_committer_default_path(self):
        """Test AetherDnaCommitter uses PROJECT_ROOT by default."""
        committer = AetherDnaCommitter()
        self.assertEqual(committer.workspace_root, str(PROJECT_ROOT))
        self.assertNotEqual(committer.workspace_root, "/Users/cryptojoker710/Desktop/AetherOS")

    def test_custom_path(self):
        """Test passing a custom path works."""
        custom_path = "/tmp/custom/path"
        sandbox = AetherHeuristicSandbox(workspace_root=custom_path)
        self.assertEqual(sandbox.workspace_root, custom_path)

        committer = AetherDnaCommitter(workspace_root=custom_path)
        self.assertEqual(committer.workspace_root, custom_path)

if __name__ == '__main__':
    unittest.main()
