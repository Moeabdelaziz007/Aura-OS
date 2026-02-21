import mmap
import os
import yaml
import hashlib
import asyncio
from dataclasses import dataclass
from typing import Any, Optional, Dict

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
        """Returns or creates a persistent mmap for a memory file (DNA or Nexus)."""
        if filename not in self._mmaps:
            path = os.path.join(self.memory_path, filename)
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

    def _parse_blocks(self, raw_data: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """Synchronous YAML extractor."""
        results = {}
        for filename, content in raw_data.items():
            if "```yaml" in content:
                block = content.split("```yaml")[1].split("```")[0]
                results[filename] = yaml.safe_load(block) or {}
            else:
                results[filename] = {}
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
                parsed = {}
                if "```yaml" in raw:
                    block = raw.split("```yaml")[1].split("```")[0]
                    parsed = yaml.safe_load(block) or {}
                self.nexus_cache = parsed.get("synapses", [])
                needs_update = True

            return self.nexus_cache or []

    def search_nexus(self, query: Dict[str, Any], top_k: int = 3) -> list[Dict[str, Any]]:
        """Naive similarity search over the loaded nexus nodes."""
        if not self.nexus_cache:
            # Load synchronously if not yet available
            # (caller assumed to have called load_nexus_async earlier)
            return []
        # placeholder: return first k entries for now
        return self.nexus_cache[:top_k]

if __name__ == "__main__":
    # Quick sanity check
    navigator = AuraNavigator()
    async def test():
        dna = await navigator.load_dna_async()
        print(f"⚡ AuraNavigator Active (v{dna.version})")
        nexus = await navigator.load_nexus_async()
        print(f"🔗 Nexus nodes: {len(nexus)}")
    asyncio.run(test())
