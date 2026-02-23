import asyncio
import os
import logging
from agent.forge.cloud_nexus import CloudNexus

logging.basicConfig(level=logging.INFO)

async def test_genesis_connection():
    print("🚀 AetherOS: Initiating New Genesis Connection Test...")
    
    project_id = "notional-armor-456623-e8"
    key_path = ".idx/aether-key.json"
    
    if not os.path.exists(key_path):
        print(f"❌ Error: Key file not found at {key_path}")
        return

    nexus = CloudNexus(project_id, key_path)
    
    print("📡 Writing UI-to-API shadow map to 'SharedShadowMaps'...")
    await nexus.share_shadow_map(
        service="Coingecko_V3",
        base_url="https://api.coingecko.com/api/v3",
        intent_action="price_discovery"
    )
    
    print("🔍 Immediately reading back from the Global Pool...")
    pattern = await nexus.discover_global_patterns("Coingecko_V3")
    
    if pattern:
        print(f"✅ Data Flow Verified! Pattern: {pattern}")
    else:
        print("❌ Data Flow Failed: Document not found.")

if __name__ == "__main__":
    asyncio.run(test_genesis_connection())
