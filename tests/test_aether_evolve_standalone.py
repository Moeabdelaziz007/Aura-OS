import asyncio
import os
from agent.aether_orchestrator.aether_evolve import monitor, evolve_engine

async def main():
    print("🔬 Starting AetherEvolve Standalone Test...")
    
    # Simulate an anomaly
    anomaly = {
        "component": "Orchestrator",
        "error_type": "ZeroDivisionError",
        "message": "division by zero"
    }
    
    # The file we want to fix
    target_file = "agent/orchestrator/main.py"
    
    print(f"🧬 Triggering healing for {target_file}...")
    await evolve_engine.trigger_healing(anomaly, target_file)
    print("🏁 Test complete.")

if __name__ == "__main__":
    asyncio.run(main())
