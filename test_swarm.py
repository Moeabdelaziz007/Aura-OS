import asyncio
import os
import logging
from agent.forge.aether_forge import AetherForge

# Configure logging to see the Swarm Cache hits
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | 🧪 Test | %(levelname)s | %(message)s"
)
logger = logging.getLogger("SwarmTest")

async def verify_swarm_intelligence():
    print("\n" + "━"*60)
    print("🧠 AETHER OS: SWARM INTELLIGENCE VERIFICATION")
    print("   Testing Global Knowledge Synchronization...")
    print("━"*60 + "\n")

    # Ensure environment is set
    os.environ["GOOGLE_CLOUD_PROJECT"] = "notional-armor-456623-e8"
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = ".idx/aether-key.json"

    # 1. Agent A: Discovery Phase
    print("🤖 Agent A: Initializing and Discovering 'Solana_Price'...")
    async with AetherForge() as forge_a:
        intent_a = {
            "service": "coingecko", 
            "params": {"coins": ["solana"], "currencies": ["usd"]}
        }
        res_a = await forge_a.forge_and_deploy(intent_a)
        print(f"✅ Agent A Result: {res_a.success} | Latency: {res_a.execution_ms:.2f}ms")
    
    # Wait for async cloud share to propagate
    print("⏳ Synchronizing with Hive Mind...")
    await asyncio.sleep(3)

    # 2. Agent B: Retrieval Phase
    print("\n🤖 Agent B: Querying Hive Mind for 'Solana_Price'...")
    async with AetherForge() as forge_b:
        intent_b = {
            "service": "coingecko", 
            "params": {"coins": ["solana"], "currencies": ["usd"]}
        }
        # Agent B should see the 'Swarm Cache HIT' log in the console if integrated correctly
        res_b = await forge_b.forge_and_deploy(intent_b)
        print(f"✅ Agent B Result: {res_b.success} | Latency: {res_b.execution_ms:.2f}ms")
        
    print("\n" + "━"*60)
    print("✨ Swarm Intelligence Test Complete.")
    print("━"*60 + "\n")

if __name__ == "__main__":
    asyncio.run(verify_swarm_intelligence())
