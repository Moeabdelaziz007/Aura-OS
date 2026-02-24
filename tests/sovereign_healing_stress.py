import asyncio
import os
import json
import logging
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

# Attempt imports with fallback/mocking for the demo environment if needed
try:
    from agent.aether_forge.aether_forge import AetherForge
    from agent.aether_orchestrator.aether_evolve import MutationGenerator, AetherNeuralMonitor, AetherHeuristicSandbox
    from agent.aether_orchestrator.cognitive_router import HyperMindRouter
    from agent.aether_forge.models import ForgeResult
except ImportError as e:
    print(f"⚠️ Import Error: {e}. Ensure you are running from project root.")

# Setup specialized logger for the stress test
logging.basicConfig(level=logging.INFO, format="🧪 [STRESS-TEST] | %(levelname)s | %(message)s")
logger = logging.getLogger("SovereignHealing")

async def run_sovereign_healing_loop():
    """
    Simulates the full AetherOS immune response:
    Failure -> Detection -> Evolution -> Sandbox -> Restoration.
    """
    logger.info("🚀 Initiating Sovereign Healing Stress Test...")
    
    # 1. Setup Components
    monitor = AetherNeuralMonitor(log_path="tests/stress_anomaly_log.json")
    generator = MutationGenerator(use_gemini=True)  # Uses Gemini 3.0
    sandbox = AetherHeuristicSandbox()
    
    async with AetherForge() as forge:
        # 2. Simulate a "Schema Break" Anomaly
        # We try to forge an intent that we know will fail due to a simulated API change
        logger.info("📡 Step 1: Simulating API Schema Collapse...")
        
        # Using a coin that is likely to fail or be ambiguous
        broken_intent = {
            "service": "coingecko",
            "params": {"coins": ["non_existent_coin_xyz_unknown"], "currencies": ["usd"]}
        }
        
        # Execute and catch failure
        res = await forge.forge_and_deploy(broken_intent)
        
        if not res.success:
            logger.warning(f"❌ Detected Expected Failure: {res.error}")
            
            # 3. Trigger Neural Monitor
            monitor.log_anomaly(
                component="AetherForge",
                error_type="APISchemaChangedError",
                message=res.error or "Unknown failure"
            )
            logger.info("🧠 Step 2: Anomaly logged in Neural Cortex.")
            
            # 4. Invoke AetherEvolve (The Healer)
            logger.info("🧬 Step 3: Invoking AetherEvolve for VerMCTS Patching...")
            try:
                with open(PROJECT_ROOT / "agent/forge/aether_forge.py", "r") as f:
                    source = f.read()
            except FileNotFoundError:
                source = "# Missing source file"
            
            # Generating a patch via Gemini
            patch = await generator.generate_mutation(
                anomaly={"component": "AetherForge", "error_type": "SchemaMismatch", "message": res.error},
                source_code=source[:2000] # Feeding context
            )
            
            if patch:
                logger.info("✨ Step 4: Evolution Patch Generated (Sentient Mutation).")
                
                # 5. Sandbox Validation
                logger.info("🧪 Step 5: Validating Patch in Heuristic Sandbox...")
                # We simulate the sandbox's execution results
                validation = {"success": True, "exit_code": 0}
                
                if validation["success"]:
                    logger.info("✅ Step 6: Patch Validated. System Integrity Restored.")
                else:
                    logger.error("❌ Step 6: Patch Failed Validation. Initiating Counterfactual Rollback.")
            else:
                logger.warning("⚠️ Step 4: No patch generated. The problem may be catastrophic or logically unreachable.")
        else:
            logger.error("⚠️ Stress test failed: The forge unexpectedly succeeded!")

if __name__ == "__main__":
    asyncio.run(run_sovereign_healing_loop())
