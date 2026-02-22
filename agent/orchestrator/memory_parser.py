import mmap
import os
import hashlib
import asyncio
import numpy as np
from dataclasses import dataclass
from typing import Any, Optional, Dict, List
try:
    from sentence_transformers import SentenceTransformer
    import faiss
except ImportError:
    SentenceTransformer = None
    faiss = None

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

class VectorEncoder:
    """Encodes text into 384-dimensional latent space using all-MiniLM-L6-v2."""
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if SentenceTransformer:
            print(f"🧠 VectorNexus: Loading transformer model {model_name}...")
            self.model = SentenceTransformer(model_name)
        else:
            print("⚠️ VectorNexus: sentence-transformers not found. Semantic memory disabled.")
            self.model = None

    def encode(self, text: str) -> np.ndarray:
        if not self.model:
            return np.zeros(384, dtype="float32")
        return self.model.encode(text, convert_to_numpy=True).astype("float32")

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
        
        # Vector Nexus Init
        self.encoder = VectorEncoder()
        self.index: Optional[faiss.IndexFlatIP] = None  # Inner Product for Cosine Similarity
        self.indexed_nodes: List[Dict[str, Any]] = []
        self.dna_files = [
            "SOUL.md", "WORLD.md", "INFERENCE.md", "AGENTS.md", 
            "CAUSAL.md", "EVOLVE.md", "PULSE.md", "SKILLS.md", 
            "TOPOLOGY.md", "MEMORY.md"
        ]
        self.nexus_file = "NEXUS.md"

    def _create_mmap_blocking(self, path: str):
        """Helper to perform blocking file I/O in a thread."""
        # ensure directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.exists(path):
            # create empty file
            with open(path, "w") as f:
                f.write("\n")
        f = open(path, "r+b")
        mm = mmap.mmap(f.fileno(), 0)
        return f, mm

    async def _get_mmap_async(self, filename: str) -> mmap.mmap:
        """Returns or creates a persistent mmap for a memory file (DNA or Nexus).

        If the file does not exist, it is created as an empty markdown document so
        that the rest of the system can operate without crashing.
        """
        if filename not in self._mmaps:
            path = os.path.join(self.memory_path, filename)

            # Offload blocking file operations to a thread
            f, mm = await asyncio.to_thread(self._create_mmap_blocking, path)

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
                mm = await self._get_mmap_async(dna_file)
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
            try:
                block = content.split("```yaml")[1].split("```")[0]
                return yaml.safe_load(block) or {}
            except Exception:
                return {}
        return {}

    def _parse_blocks(self, raw_data: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """Synchronous YAML extractor. Merges all YAML blocks found in a file."""
        results = {}
        for filename, content in raw_data.items():
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
        return results

    async def close(self):
        """Cleanup mmaps and file handles on system shutdown."""
        # Close all memory-mapped files
        for filename, mm in list(self._mmaps.items()):
            try:
                mm.close()
                print(f"🧹 Closed mmap for {filename}")
            except Exception as e:
                print(f"⚠️ Error closing mmap for {filename}: {e}")
        
        # Close all file handles
        for filename, f in list(self._file_handles.items()):
            try:
                f.close()
                print(f"🧹 Closed file handle for {filename}")
            except Exception as e:
                print(f"⚠️ Error closing file handle for {filename}: {e}")
        
        # Clear dictionaries
        self._mmaps.clear()
        self._file_handles.clear()
        self._hashes.clear()
        self.dna_cache = None
        self.nexus_cache = None
        
        print("✅ AuraNavigator: All resources released")

    # --- Nexus helpers --------------------------------------------------
    async def load_nexus_async(self, force: bool = False) -> list[Dict[str, Any]]:
        """Loads the Aura-Nexus graph from NEXUS.md."""
        async with self._lock:
            needs_update = False
            mm = await self._get_mmap_async(self.nexus_file)
            mm.seek(0)
            content_bytes = mm.read()
            current_hash = self._calculate_hash(content_bytes)

            if force or current_hash != self._hashes.get(self.nexus_file):
                self._hashes[self.nexus_file] = current_hash
                raw = content_bytes.decode("utf-8")
                # Move blocking YAML parsing to a background thread
                parsed = await asyncio.to_thread(self._parse_single_block, raw)
                self.nexus_cache = parsed.get("synapses", [])
                
                # Update Vector Index
                if self.nexus_cache and self.encoder.model:
                    await self._refresh_vector_index()
                
                needs_update = True

            return self.nexus_cache or []

    async def _refresh_vector_index(self):
        """Builds a FAISS index from the metadata/descriptions in NEXUS.md."""
        if not self.nexus_cache or not self.encoder.model:
            return

        print(f"🔗 VectorNexus: Indexing {len(self.nexus_cache)} synapses...")
        
        texts = []
        for node in self.nexus_cache:
            # Create a rich text representation for embedding
            meta = node.get("metadata", {})
            desc = f"{node.get('id', '')} {meta.get('desc', '')} {meta.get('intent', '')}"
            texts.append(desc)
            
        embeddings = await asyncio.to_thread(self.encoder.encode, texts)
        
        # FAISS normalization for Cosine Similarity (IP on normalized vectors)
        faiss.normalize_L2(embeddings)
        
        d = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(d)
        self.index.add(embeddings)
        self.indexed_nodes = self.nexus_cache
        print(f"✅ VectorNexus: FAISS Index synchronized ({len(self.indexed_nodes)} nodes)")

    async def search_nexus(self, query_text: str, top_k: int = 3) -> list[Dict[str, Any]]:
        """Semantic similarity search via FAISS and Latent Space encoding."""
        if self.nexus_cache is None:
            await self.load_nexus_async()

        if not self.index or not self.encoder.model:
            # Fallback to naive search if indexing failed
            print("⚠️ VectorNexus: Semantic index missing, falling back to naive search.")
            return (self.nexus_cache or [])[:top_k]

        # Embed query
        query_vec = await asyncio.to_thread(self.encoder.encode, [query_text])
        faiss.normalize_L2(query_vec)
        
        # Search index
        scores, indices = self.index.search(query_vec, top_k)
        
        results = []
        for i, score in zip(indices[0], scores[0]):
            if i != -1 and i < len(self.indexed_nodes):
                node = self.indexed_nodes[i].copy()
                node["_score"] = float(score)
                results.append(node)
        
        return results

if __name__ == "__main__":
    # Quick sanity check
    navigator = AuraNavigator()
    async def test():
        dna = await navigator.load_dna_async()
        print(f"⚡ AuraNavigator Active (v{dna.version})")
        nexus = await navigator.load_nexus_async()
        print(f"🔗 Nexus nodes: {len(nexus)}")
    asyncio.run(test())
