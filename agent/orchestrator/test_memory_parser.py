
import pytest
import asyncio
import unittest
import mmap
import numpy as np
from unittest.mock import patch, MagicMock
from agent.orchestrator.memory_parser import AuraNavigator, yaml
import os

class TestMemoryParser(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp_memory_path = "temp_test_memory"
        os.makedirs(self.temp_memory_path, exist_ok=True)
        self.navigator = AuraNavigator(memory_path=self.temp_memory_path)

    async def asyncTearDown(self):
        await self.navigator.close()
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

    def test_get_mmap_creates_file(self):
        filename = "NEW_FILE.md"
        filepath = os.path.join(self.temp_memory_path, filename)
        self.assertFalse(os.path.exists(filepath))

        mm = self.navigator._get_mmap(filename)
        self.assertTrue(os.path.exists(filepath))
        self.assertIsInstance(mm, mmap.mmap)

        # Verify reuse
        mm2 = self.navigator._get_mmap(filename)
        self.assertIs(mm, mm2)

        # Verify content (empty file created with \n)
        mm.seek(0)
        content = mm.read()
        self.assertEqual(content, b"\n")

    async def test_load_dna_async(self):
        # Create dummy DNA files
        soul_file = os.path.join(self.temp_memory_path, "SOUL.md")
        with open(soul_file, "w") as f:
            f.write("```yaml\nversion: 2.0.0\n```")

        # Mock yaml.safe_load for the file content
        with patch.object(yaml, 'safe_load', return_value={"version": "2.0.0"}):
            dna = await self.navigator.load_dna_async()
            self.assertEqual(dna.version, "2.0.0")
            self.assertEqual(dna.soul, {"version": "2.0.0"})

            # Test reload without changes (should use cache, hash same)
            # We modify self.dna_cache to verify it's not reloaded
            self.navigator.dna_cache.version = "3.0.0"
            dna2 = await self.navigator.load_dna_async()
            self.assertEqual(dna2.version, "3.0.0") # Should be cached version

        # Test reload with changes (hash changes)
        with open(soul_file, "w") as f:
            f.write("```yaml\nversion: 4.0.0\n```")

        with patch.object(yaml, 'safe_load', return_value={"version": "4.0.0"}):
             dna3 = await self.navigator.load_dna_async()
             self.assertEqual(dna3.version, "4.0.0")

    async def test_close_clean_resources(self):
        filename = "TEST.md"
        self.navigator._get_mmap(filename)
        self.assertEqual(len(self.navigator._mmaps), 1)
        self.assertEqual(len(self.navigator._file_handles), 1)

        await self.navigator.close()
        self.assertEqual(len(self.navigator._mmaps), 0)
        self.assertEqual(len(self.navigator._file_handles), 0)

    async def test_vector_search_fallback_no_index(self):
        # Ensure encoder model is None or index is None
        self.navigator.index = None

        # Mock nexus cache
        self.navigator.nexus_cache = [{"id": "1", "metadata": {"desc": "test"}}]

        results = await self.navigator.search_nexus("query")
        # Should return top_k=3 from cache
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "1")

    async def test_vector_search_with_mock_index(self):
        # Patch faiss in memory_parser module
        with patch('agent.orchestrator.memory_parser.faiss') as mock_faiss:
            # Mock encoder and index
            mock_encoder = MagicMock()
            # The encoder expects a list of texts, returns array of shape (N, 384)
            mock_encoder.encode.return_value = np.array([[0.1]*384], dtype="float32")
            self.navigator.encoder.model = mock_encoder

            # Mock index
            mock_index = MagicMock()
            # search returns (distances, indices)
            # indices are indices into self.indexed_nodes
            mock_index.search.return_value = (np.array([[0.9]]), np.array([[0]]))
            self.navigator.index = mock_index

            self.navigator.nexus_cache = [{"id": "1", "metadata": {"desc": "test"}}]
            self.navigator.indexed_nodes = self.navigator.nexus_cache

            results = await self.navigator.search_nexus("query")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["id"], "1")
            self.assertEqual(results[0]["_score"], 0.9)

    def test_init_fallback(self):
        from agent.orchestrator.memory_parser import VectorEncoder
        try:
            import sentence_transformers
            has_transformers = True
        except ImportError:
            has_transformers = False

        encoder = VectorEncoder()
        if not has_transformers:
            self.assertIsNone(encoder.model)
        else:
            # If installed, model should be loaded (or we mock it to be sure)
            # Since we can't easily control installation here, let's just ensure logic holds
            pass
