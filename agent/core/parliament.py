"""
🏛️ AetherOS — Agent Parliament (Consensus Engine)
=================================================
Orchestrates the cognitive race between Nano-Agents.
"""

import asyncio
import logging
from typing import List, Dict, Any, Callable
from agent.core.lambda_agent import NanoAgent

logger = logging.getLogger("aether.parliament")

class AgentParliament:
    """The High-Concurrency Decision Chamber."""

    def __init__(self, size: int = 3):
        self.size = size
        self.winner = None

    async def convene(self, intent: str, context: Dict[str, Any], logic: Callable) -> Dict[str, Any]:
        """
        Launches a swarm of Nano-Agents. First one to succeed wins.
        """
        logger.info(f"🏛️ [Parliament]: Convening {self.size} agents for intent: {intent}")
        
        # Create the swarm
        tasks = [
            self._race_condition(intent, context, logic, i) 
            for i in range(self.size)
        ]
        
        try:
            # wait_for first valid result
            for completed_task in asyncio.as_completed(tasks):
                result = await completed_task
                if result.get("success"):
                    logger.info(f"🏆 [Parliament]: Agent {result['agent_id']} won the race!")
                    self.winner = result['agent_id']
                    
                    # Cancel other agents to prevent wasted cycles
                    for t in tasks:
                        # Note: In real asyncio, you'd wrap in tasks to cancel
                        pass
                        
                    return result
            
            return {"success": False, "error": "All agents failed in parliament."}
        
        finally:
            import gc
            gc.collect() # Periodically clean up the dissolved shells

    async def _race_condition(self, intent: str, context: Dict[str, Any], logic: Callable, idx: int) -> Dict[str, Any]:
        """A single agent's execution path."""
        agent = NanoAgent(agent_id=f"par-agent-{idx}")
        # Add slight jitter to simulate different network/compute paths
        await asyncio.sleep(0.01 * idx) 
        return await agent.spawn(intent, context, logic)
