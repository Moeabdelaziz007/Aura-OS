import asyncio
import websockets
import json

async def trigger_poison():
    uri = "ws://127.0.0.1:8000"
    async with websockets.connect(uri) as websocket:
        # Synaptic message with poison signal
        msg = {
            "data": {
                "poison": "NEURAL_POISON"
            }
        }
        print(f"📡 Sending Poison Signal to {uri}...")
        await websocket.send(json.dumps(msg))
        
        # Wait for potential response or crash log
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            print(f"📩 Response: {response}")
        except asyncio.TimeoutError:
            print("⏳ Connection timed out (likely due to simulated crash)")
        except Exception as e:
            print(f"💀 Connection lost: {e}")

if __name__ == "__main__":
    asyncio.run(trigger_poison())
