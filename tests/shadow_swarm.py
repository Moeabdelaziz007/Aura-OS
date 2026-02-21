"""Mock swarm execution for CI (shadow mode).

This script mimics the behavior of QuantumWeaver nodes without launching
real Cloud Run jobs or Playwright browsers. It allows the CI pipeline to
exercise orchestration logic without burning cloud credits.
"""

import os
import json
import random


def run_mock_node(state: str, objective: str):
    # pretend to compute an EFE based on state complexity
    efe = random.uniform(0.0, 1.0)
    result = {
        "trajectory_id": os.getenv("MOCK_NODE_ID", "shadow-0"),
        "success": True,
        "free_energy_cost": efe,
        "action_sequence": ["MOCK_ACTION"]
    }
    print(f"RESULT: {json.dumps(result)}")


if __name__ == "__main__":
    # accepted CLI arguments for compatibility with real node
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", required=False, default="{}")
    parser.add_argument("--objective", required=False, default="test")
    args = parser.parse_args()
    run_mock_node(args.state, args.objective)
