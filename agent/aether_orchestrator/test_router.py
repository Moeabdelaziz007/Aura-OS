"""
Test script for HyperMindRouter and AetherNavigator.

Run this script as a module from the project root:
    python -m agent.orchestrator.test_router
"""

import sys
from unittest.mock import MagicMock
sys.modules["numpy"] = MagicMock()
import asyncio

from .memory_parser import AetherNavigator
from .cognitive_router import HyperMindRouter

async def main():
    bridge = AetherNavigator()
    router = HyperMindRouter(bridge)
    
    print("🔬 Testing HyperMindRouter Gating Logic and AetherNavigator...")
    
    # Test Case 1: Low Anomaly (Reflexive)
    print("\nCase 1: Low Anomaly (Expected outcome: SYSTEM_1_REFLEX)")
    ctx_low = {"anomaly": 0.05, "novelty": 0.1, "goal_alignment": 1.0}
    action1 = await router.route_action(ctx_low)
    print(f"Result: {action1}")
    
    # Test Case 2: High Anomaly (Reflective)
    print("\nCase 2: High Anomaly (Expected outcome: SYSTEM_2_SWARM)")
    ctx_high = {"anomaly": 0.8, "novelty": 0.5, "goal_alignment": 0.5}
    action2 = await router.route_action(ctx_high)
    print(f"Result: {action2}")
    
    # Test Case 3: EFE Calculation
    print("\nCase 3: Calculating EFE (G)...")
    g_score = await router.calculate_efe(ctx_high)
    print(f"EFE (G-Score): {g_score:.4f}")

    # Test nexus search (should gracefully return list)
    print("\nCase 4: Nexus Search")
    hits = await router.bridge.search_nexus({"dummy": True})
    print(f"Nexus hits: {hits}")

    await bridge.close()

if __name__ == "__main__":
    asyncio.run(main())
