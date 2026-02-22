
import pytest
import asyncio
import unittest
from unittest.mock import patch, MagicMock
from agent.orchestrator.memory_parser import AuraNavigator, yaml
import os

class TestMemoryParser(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp_memory_path = "temp_test_memory"
        os.makedirs(self.temp_memory_path, exist_ok=True)
        self.navigator = AuraNavigator(memory_path=self.temp_memory_path)

    def tearDown(self):
        self.navigator.close()
        import shutil
        shutil.rmtree(self.temp_memory_path)

    def test_parse_blocks_valid_yaml(self):
        raw_data = {
            "SOUL.md": "```yaml\nversion: 1.0.0\n```"
        }
        # Note: We mock yaml.safe_load because the production environment
        # might not have PyYAML installed, and we want to test the
        # Navigator's logic independent of the YAML library's presence.
        with patch.object(yaml, 'safe_load', return_value={"version": "1.0.0"}):
            results = self.navigator._parse_blocks(raw_data)
            assert results["SOUL.md"] == {"version": "1.0.0"}

    def test_parse_blocks_no_yaml(self):
        raw_data = {
            "SOUL.md": "Just some text"
        }
        results = self.navigator._parse_blocks(raw_data)
        assert results["SOUL.md"] == {}

    def test_parse_blocks_invalid_yaml_handled(self):
        raw_data = {
            "SOUL.md": "```yaml\ninvalid: [ yaml: structure\n```"
        }
        with patch.object(yaml, 'safe_load', side_effect=Exception("YAML Error")):
            # Should now return {} instead of raising
            results = self.navigator._parse_blocks(raw_data)
            assert results["SOUL.md"] == {}

    async def test_load_nexus_async_invalid_yaml_handled(self):
        nexus_file = os.path.join(self.temp_memory_path, "NEXUS.md")
        with open(nexus_file, "w") as f:
            f.write("```yaml\ninvalid: [ yaml\n```")

        with patch.object(yaml, 'safe_load', side_effect=Exception("YAML Error")):
            # Should now return [] (empty synapses) instead of raising
            nodes = await self.navigator.load_nexus_async(force=True)
            assert nodes == []

    async def test_load_nexus_async_valid_yaml(self):
        nexus_file = os.path.join(self.temp_memory_path, "NEXUS.md")
        with open(nexus_file, "w") as f:
            f.write("```yaml\nsynapses: [{id: 1}]\n```")

        with patch.object(yaml, 'safe_load', return_value={"synapses": [{"id": 1}]}):
            nodes = await self.navigator.load_nexus_async(force=True)
            assert nodes == [{"id": 1}]
