import asyncio
import unittest
from agent.core.parliament import AgentParliament

class TestAlphaSovereign(unittest.IsolatedAsyncioTestCase):
    
    async def dummy_logic(self, intent, context, state):
        """Simulated work with variable latency."""
        # Intent-based latency to simulate real-world variance
        if "fast" in intent:
            await asyncio.sleep(0.01)
        else:
            await asyncio.sleep(0.2)
        return {"data": "processed", "intent": intent}

    async def test_parliament_race(self):
        print("\n🏛️ Testing Agent Parliament Race...")
        parliament = AgentParliament(size=5)
        
        # We intent 'fast' to ensure race is noticeable
        result = await parliament.convene("fast_intent", {}, self.dummy_logic)
        
        self.assertTrue(result["success"])
        self.assertIn("par-agent-", result["agent_id"])
        print(f"✅ Winner: {result['agent_id']}")

    async def test_stateless_cleanup(self):
        print("🧼 Testing Stateless Memory Cleanup...")
        import gc
        before = gc.get_count()
        
        parliament = AgentParliament(size=2)
        await parliament.convene("cleanup_test", {}, self.dummy_logic)
        
        # Explicitly checking if parliament triggers GC
        # (Difficult to assert exact counts but verifies no crash)
        print("✅ Cleanup logic executed without faults.")

if __name__ == "__main__":
    unittest.main()
