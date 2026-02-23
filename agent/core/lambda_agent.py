"""
🧠 AetherOS — NanoAgent (Stateless Lambda Core)
==============================================
Ephemeral coroutines designed for high-concurrency and zero-memory footprint.
"""

import asyncio
import logging
import uuid
from typing import Any, Dict, Optional, Callable
from agent.forge.cloud_nexus import CloudNexus

logger = logging.getLogger("aether.lambda")

class NanoAgent:
    """The Fundamental Stateless Unit of AetherOS."""

    def __init__(self, agent_id: Optional[str] = None):
        self.id = agent_id or f"nano-{uuid.uuid4().short}"
        self.nexus = CloudNexus()
        self._state = {}

    async def spawn(self, intent: str, context: Dict[str, Any], logic: Callable) -> Dict[str, Any]:
        """
        Spawns the agent, hydrates state from Nexus, executes logic, 
        syncs final state, and dissolves.
        """
        logger.info(f"🧬 [NanoAgent {self.id}]: Spawning for intent: {intent}")
        
        try:
            # 1. Hydration (Stateless -> Contextual)
            self._state = await self._hydrate(intent)
            
            # 2. Execution (The Cognitive Work)
            result = await logic(intent, context, self._state)
            
            # 3. Dehydration (Consistency Loop)
            await self._dehydrate(self._state)
            
            return {
                "agent_id": self.id,
                "success": True,
                "result": result
            }
        except Exception as e:
            logger.error(f"💥 [NanoAgent {self.id}] Execution Fault: {e}")
            return {"agent_id": self.id, "success": False, "error": str(e)}
        finally:
            await self.dissolve()

    async def _hydrate(self, intent: str) -> Dict[str, Any]:
        """Fetches persistent DNA/State from Firestore."""
        # In a real impl, this uses KNN to find relevant historical state
        return await self.nexus.get_agent_context(self.id) or {}

    async def _dehydrate(self, state: Dict[str, Any]):
        """Persists state changes back to Firestore."""
        await self.nexus.update_agent_context(self.id, state)

    async def dissolve(self):
        """Zero-Friction Cleanup."""
        logger.info(f"🫧 [NanoAgent {self.id}]: Dissolving into ether.")
        self._state = None
        self.nexus = None
        # Explicitly aid GC (though not strictly necessary for local scopes)
        import gc
        # gc.collect() # Triggered by the Parliament instead to batch cleanup
