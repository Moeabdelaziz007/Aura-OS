import mmap
import os
import hashlib
import asyncio
from dataclasses import dataclass
from typing import Any, Optional, Dict

# Optional YAML import with graceful fallback (parses to empty dicts if missing)
try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    class _YamlStub:
        @staticmethod
        def safe_load(_):
            return {}
    yaml = _YamlStub()  # type: ignore

@dataclass
class DNABelief:
    soul: dict[str, Any]
    world: dict[str, Any]
    inference: dict[str, Any]
    agents: dict[str, Any]
    causal: dict[str, Any]
    evolve: dict[str, Any]
    pulse: dict[str, Any]
    skills: dict[str, Any]
    topology: dict[str, Any]
    memory: dict[str, Any]
    version: str

class AuraNavigator:
    """
    Priority 0 Refactor: AuraNavigator (formerly PersistentMemoryBridge).
    Navigates the DNA and the new Aura-Nexus graph in zero latency.
    """
    def __init__(self, memory_path: str = "agent/memory/"):
        self.memory_path = memory_path
        self._mmaps: Dict[str, mmap.mmap] = {}
        self._file_handles: Dict[str, Any] = {}
        self._hashes: Dict[str, str] = {}
        self.dna_cache: Optional[DNABelief] = None
        self.nexus_cache: Optional[list[Dict[str, Any]]] = None
        self._lock = asyncio.Lock()
        self.dna_files = [
            "SOUL.md", "WORLD.md", "INFERENCE.md", "AGENTS.md", 
            "CAUSAL.md", "EVOLVE.md", "PULSE.md", "SKILLS.md", 
            "TOPOLOGY.md", "MEMORY.md"
        ]
        self.nexus_file = "NEXUS.md"

    def _get_mmap(self, filename: str) -> mmap.mmap:
        """Returns or creates a persistent mmap for a memory file (DNA or Nexus).

        If the file does not exist, it is created as an empty markdown document so
        that the rest of the system can operate without crashing.
        """
        if filename not in self._mmaps:
            path = os.path.join(self.memory_path, filename)
            # ensure directory exists
            os.makedirs(self.memory_path, exist_ok=True)
            if not os.path.exists(path):
                # create empty file
                with open(path, "w") as f:
                    f.write("\n")
            f = open(path, "r+b")
            mm = mmap.mmap(f.fileno(), 0)
            self._file_handles[filename] = f
            self._mmaps[filename] = mm
        return self._mmaps[filename]

    def _calculate_hash(self, data: bytes) -> str:
        return hashlib.md5(data).hexdigest()

    async def load_dna_async(self, force: bool = False) -> DNABelief:
        """Loads and parses DNA without blocking the event loop."""
        async with self._lock:
            needs_update = False
            raw_contents = {}

            for dna_file in self.dna_files:
                mm = self._get_mmap(dna_file)
                mm.seek(0)
                content_bytes = mm.read()
                current_hash = self._calculate_hash(content_bytes)

                if force or current_hash != self._hashes.get(dna_file):
                    self._hashes[dna_file] = current_hash
                    raw_contents[dna_file] = content_bytes.decode("utf-8")
                    needs_update = True

            if needs_update:
                # Move blocking YAML parsing to a background thread
                parsed = await asyncio.to_thread(self._parse_blocks, raw_contents)
                
                self.dna_cache = DNABelief(
                    soul=parsed.get("SOUL.md", {}),
                    world=parsed.get("WORLD.md", {}),
                    inference=parsed.get("INFERENCE.md", {}),
                    agents=parsed.get("AGENTS.md", {}),
                    causal=parsed.get("CAUSAL.md", {}),
                    evolve=parsed.get("EVOLVE.md", {}),
                    pulse=parsed.get("PULSE.md", {}),
                    skills=parsed.get("SKILLS.md", {}),
                    topology=parsed.get("TOPOLOGY.md", {}),
                    memory=parsed.get("MEMORY.md", {}),
                    version=parsed.get("SOUL.md", {}).get("version", "0.0.0")
                )
            
            return self.dna_cache

    def _parse_single_block(self, content: str) -> Dict[str, Any]:
        """Synchronous YAML extractor for a single block."""
        if "```yaml" in content:
            block = content.split("```yaml")[1].split("```")[0]
            return yaml.safe_load(block) or {}
        return {}

    def _parse_blocks(self, raw_data: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """Synchronous YAML extractor. Merges all YAML blocks found in a file."""
        results = {}
        for filename, content in raw_data.items():
 improve-yaml-parsing-tests-10655427900937424656
            if "```yaml" in content:
                try:
                    block = content.split("```yaml")[1].split("```")[0]
                    results[filename] = yaml.safe_load(block) or {}
                except Exception:
                    results[filename] = {}
            else:
                results[filename] = {}
=======
 optimize-yaml-parsing-16978240279472154414
            results[filename] = self._parse_single_block(content)
=======
            merged_data = {}
            parts = content.split("```yaml")
            # Skip the first part as it's before the first yaml block
            for part in parts[1:]:
                if "```" in part:
                    block = part.split("```")[0]
                    try:
                        data = yaml.safe_load(block)
                        if isinstance(data, dict):
                            merged_data.update(data)
                    except Exception:
                        pass
            results[filename] = merged_data
 main
 main
        return results

    def close(self):
        """Cleanup mmaps and file handles on system shutdown."""
        for mm in self._mmaps.values():
            mm.close()
        for f in self._file_handles.values():
            f.close()

    # --- Nexus helpers --------------------------------------------------
    async def load_nexus_async(self, force: bool = False) -> list[Dict[str, Any]]:
        """Loads the Aura-Nexus graph from NEXUS.md."""
        async with self._lock:
            needs_update = False
            mm = self._get_mmap(self.nexus_file)
            mm.seek(0)
            content_bytes = mm.read()
            current_hash = self._calculate_hash(content_bytes)

            if force or current_hash != self._hashes.get(self.nexus_file):
                self._hashes[self.nexus_file] = current_hash
                raw = content_bytes.decode("utf-8")
 improve-yaml-parsing-tests-10655427900937424656
                parsed = {}
                if "```yaml" in raw:
                    try:
                        block = raw.split("```yaml")[1].split("```")[0]
                        parsed = yaml.safe_load(block) or {}
                    except Exception:
                        parsed = {}
=======
                # Move blocking YAML parsing to a background thread
                parsed = await asyncio.to_thread(self._parse_single_block, raw)
 main
                self.nexus_cache = parsed.get("synapses", [])
                needs_update = True

            return self.nexus_cache or []

    async def search_nexus(self, query: Dict[str, Any], top_k: int = 3) -> list[Dict[str, Any]]:
        """Naive similarity search over the loaded nexus nodes.

        If the nexus has not yet been loaded, this method will attempt an
        asynchronous load to avoid blocking the event loop.
        """
        if self.nexus_cache is None:
            await self.load_nexus_async()

        # placeholder: return first k entries for now
        return (self.nexus_cache or [])[:top_k]

if __name__ == "__main__":
    # Quick sanity check
    navigator = AuraNavigator()
    async def test():
        dna = await navigator.load_dna_async()
        print(f"⚡ AuraNavigator Active (v{dna.version})")
        nexus = await navigator.load_nexus_async()
        print(f"🔗 Nexus nodes: {len(nexus)}")
    asyncio.run(test())
