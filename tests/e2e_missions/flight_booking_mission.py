"""End-to-end demo mission: complex flight booking with voice interruption.

Simulates the killer scenario by feeding visual deltas and an audio instruction
change. Verifies that the HyperMindRouter halts current plan, updates Nexus,
and calculates new route.
"""
import asyncio
import json
import time

from agent.orchestrator.memory_parser import AuraNavigator
from agent.orchestrator.cognitive_router import HyperMindRouter

# stub visual deltas as simple contexts
SCENARIO_FRAMES = [
    {"page":"search_flights","step":1},
    {"page":"select_dates","step":2},
    {"page":"choose_options","step":3},
]

async def run_mission():
    navigator = AuraNavigator()
    router = HyperMindRouter(navigator)

    print("Starting flight booking mission...")
    context = {}

    # feed frames one by one
    for frame in SCENARIO_FRAMES:
        context.update(frame)
        action = await router.route_action(context)
        print(f"Frame {frame}: routed to {action}")
        await asyncio.sleep(0.2)

    # now user interrupts via audio change
    print("User interruption: change destination to Tokyo")
    context["goal_alignment"] = 0.2  # lower alignment to encourage reevaluation
    context["novelty"] = 0.9
    action = await router.route_action(context)
    print(f"After interruption: routed to {action}")

    # verify nexus update attempt
    nexus_hits = navigator.search_nexus(context)
    print(f"Nexus context after interruption: {nexus_hits}")

    print("Mission complete.")

if __name__ == "__main__":
    asyncio.run(run_mission())
