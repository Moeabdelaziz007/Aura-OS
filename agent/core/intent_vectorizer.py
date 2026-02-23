"""
🌀 AetherOS — IntentVectorizer (Semantic DNA)
=============================================
Maps natural language intent to high-dimensional space for semantic healing.
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np

# In a production environment, we would use vertexai.language_models.TextEmbeddingModel
# For the AetherOS prototype, we use a structured similarity fallback or mock embeddings.

logger = logging.getLogger("aether.vectorizer")

class IntentVectorizer:
    """The Semantic Compass of AetherOS."""
    
    def __init__(self, use_remote: bool = False):
        self.use_remote = use_remote
        self.embedding_dim = 768  # Standard for Gecko/Vertex
        
    async def vectorize(self, text: str) -> List[float]:
        """Converts text into a semantic vector."""
        if not self.use_remote:
            # Deterministic pseudo-embedding for local testing
            # maps text to a fixed-size vector based on char-hash
            logger.debug(f"📐 Locally vectorizing: {text}")
            seed = sum(ord(c) for c in text)
            np.random.seed(seed)
            vector = np.random.uniform(-1, 1, self.embedding_dim).tolist()
            return vector
        
        # TODO: Integration with Vertex AI TextEmbeddingModel
        # model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")
        # embeddings = model.get_embeddings([text])
        # return embeddings[0].values
        return [0.0] * self.embedding_dim

    def calculate_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        """Cosine similarity between two intent vectors."""
        a = np.array(vec_a)
        b = np.array(vec_b)
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        return dot_product / (norm_a * norm_b)

    async def get_nearest_neighbors(self, query_text: str, candidates: List[Dict[str, Any]], top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Finds the most semantically similar historical intents.
        Used for 'Semantic Healing' when an exact match fails.
        """
        query_vec = await self.vectorize(query_text)
        ranked = []
        
        for cand in candidates:
            cand_vec = cand.get("vector")
            if not cand_vec:
                continue
            
            score = self.calculate_similarity(query_vec, cand_vec)
            ranked.append({**cand, "similarity_score": score})
            
        # Sort by similarity descending
        ranked.sort(key=lambda x: x["similarity_score"], reverse=True)
        return ranked[:top_k]
