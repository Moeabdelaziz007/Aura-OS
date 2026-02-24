import asyncio
import time
import logging
from agent.aether_forge import AetherForge

# Configure logging to show timestamps with milliseconds
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d | 🔮 Debug | %(message)s",
    datefmt="%H:%M:%S"
)

async def profile_forge():
    forge = AetherForge()
    intent = {"service": "coingecko", "params": {"coins": ["bitcoin"], "currencies": ["usd"]}}
    
    print("\n" + "="*60)
    print("🔬 AETHER FORGE PROFILER")
    print("="*60 + "\n")
    
    start_total = time.time()
    
    # 1. Recall check
    t1 = time.time()
    forge.nexus.recall("coingecko")
    print(f"⏱️  Nexus Recall: {(time.time() - t1)*1000:.2f}ms")
    
    # 2. Forge Execution
    t2 = time.time()
    result = await forge.forge_and_deploy(intent)
    print(f"⏱️  Full Forge Loop: {(time.time() - t2)*1000:.2f}ms")
    
    print(f"\n✅ Total Elapsed: {(time.time() - start_total)*1000:.2f}ms")
    print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(profile_forge())
