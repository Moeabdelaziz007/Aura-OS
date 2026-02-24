"""
🌌 AetherOS: Sensory Ignition
============================
The main entry point for the real-time Multimodal Live Bridge.
"""

import asyncio
import os
import logging
from agent.aether_forge.live_bridge_v2 import AetherGeminiLiveBridgeV2

# Configure logging for the Sensory Cortex
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | 🎭 Sensory | %(levelname)s | %(message)s"
)

async def ignite_sensory_cortex():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ Error: GOOGLE_API_KEY environment variable not set.")
        return

    print("\n" + "━"*60)
    print("🎭 AETHER OS: SENSORY CORTEX ACTIVATION")
    print("   Igniting Gemini Multimodal Live Bridge...")
    print("━"*60 + "\n")

    bridge = AetherGeminiLiveBridgeV2(api_key=api_key)
    
    try:
        # Start the bi-directional stream
        await bridge.start_session()
    except KeyboardInterrupt:
        await bridge.stop()
        print("\n🛑 Sensory session terminated by user.")
    except Exception as e:
        print(f"💥 Critical Fault in Sensory Cortex: {e}")
    finally:
        print("\n✨ AetherOS Sensory Cortex offline.")

if __name__ == "__main__":
    asyncio.run(ignite_sensory_cortex())
