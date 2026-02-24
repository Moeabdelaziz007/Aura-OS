# 🤖 evolution_sandbox/swarm_node.py: The QuantumWeaver Ephemeral Agent
# Usage: python swarm_node.py --state <latent_z> --objective <goal>

import os
import pathlib
import json
import asyncio
import argparse
from playwright.async_api import async_playwright

class QuantumWeaverNode:
    """
    Ephemeral Simulator Node.
    Executes UI trajectories to calculate Expected Free Energy (G).
    """
    def __init__(self, latent_state: str, objective: str):
        self.state = json.loads(latent_state)
        self.objective = objective
        self.results = {
            "trajectory_id": os.getenv("CLOUD_RUN_TASK_INDEX", "0"),
            "success": False,
            "free_energy_cost": 0.0,
            "action_sequence": []
        }

    async def execute_trajectory(self):
        """Simulates a UI path using Playwright."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # 1. Map Latent z back to a starting URL/State (Conceptual)
            start_url = self.state.get("url", "https://google.com")
            await page.goto(start_url)
            
            print(f"🚀 Node {self.results['trajectory_id']}: Simulating Objective -> {self.objective}")
            
            # 2. Execute Policy Search (Simplified for Refactor Phase)
            # In production: This selects actions from SKILLS.md to minimize G
            try:
                # rudimentary EFE approximation using SKILLS
                # Use AETHER_SKILLS_PATH environment variable if set, otherwise use relative path
                skills_path = pathlib.Path(os.getenv("AETHER_SKILLS_PATH", "agent/aether_memory/SKILLS.md"))
                
                # If relative path doesn't exist, try to resolve from current file location
                if not skills_path.exists():
                    current_path = pathlib.Path(__file__).resolve()
                    # Handle both dev structure (nested in evolution_sandbox/) and prod structure (flat/root)
                    if current_path.parent.name == "evolution_sandbox":
                        root = current_path.parent.parent
                    else:
                        root = current_path.parent
                    skills_path = root / "agent" / "memory" / "SKILLS.md"
                
                efe = 1.0

                if skills_path.exists():
                    with open(skills_path, "r", encoding="utf-8") as f:
                        text = f.read()
                    if "function_declaration" in text:
                        # reward more skills -> lower free energy
                        count = text.count("name:")
                        efe = max(0.0, 1.0 - count * 0.01)
                self.results["free_energy_cost"] = efe

                # Simulated Interaction
                await page.screenshot(path=f"sim_{self.results['trajectory_id']}.png")
                self.results["success"] = True
                self.results["action_sequence"] = ["GOTO", "WAIT", "EXTRACT"]
            except Exception as e:
                print(f"⚠️ Simulation Failure: {e}")
                self.results["success"] = False
            
            await browser.close()
            return self.results

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", required=True)
    parser.add_argument("--objective", required=True)
    args = parser.parse_args()

    node = QuantumWeaverNode(args.state, args.objective)
    output = asyncio.run(node.execute_trajectory())
    
    # Return deterministic JSON result to Cloud Run stdout (monitored by Brain)
    print(f"RESULT: {json.dumps(output)}")
