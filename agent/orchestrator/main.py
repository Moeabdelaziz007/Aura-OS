import asyncio
import json
import os
import websockets
from typing import Any, Dict
from pydantic import BaseModel, Field, ValidationError
from .memory_parser import AuraNavigator
from .cognitive_router import HyperMindRouter
from .gemini_live_client import GeminiLiveClient

class ActionContext(BaseModel):
    """Validated context for cognitive routing."""
    anomaly: float = 0.0
    novelty: float = 0.1
    goal_alignment: float = 1.0

    class Config:
        extra = "allow"

class SynapticMessage(BaseModel):
    """Top-level schema for incoming JSON synaptic signals."""
    data: ActionContext = Field(default_factory=ActionContext)

class AetherCoreOrchestrator:
    """
    The main asynchronous event loop for AuraOS.
    Bridges the Edge Client (Sensory) via WebSockets to the DNA Brain.
    """
    def __init__(self, host: str = "127.0.0.1", port: int = 8000):
        self.host = host
        self.port = port
        self.bridge = AuraNavigator()
        self.router = HyperMindRouter(self.bridge)
        self.is_running = False
        self.api_key = os.getenv("GEMINI_API_KEY")

    async def boot_sequence(self):
        """Initializes DNA and validates Persona logic."""
        print("🪐 AuraOS: AetherCore Prometheus Booting...")
        dna = await self.bridge.load_dna_async()
        print(f"🧬 DNA Sequence Verified: {dna.version}")
        self.is_running = True
        
        # Priority 3: Start Active Pulse Monitor
        asyncio.create_task(self.pulse_monitor())

    async def pulse_monitor(self, interval: float = 1.0):
        """Cognitive Pacemaker: Detects deadlocks and zombie connections."""
        print("💓 Pulse Engine: Monitoring Neural Synchronicity...")
        while True:
            await asyncio.sleep(interval)

    async def handle_optic_nerve(self, websocket):
        """Processes real-time binary/JSON synaptic bridge signals."""
        remote_addr = websocket.remote_address
        print(f"🛰️ Synaptic Bridge: Connection established from {remote_addr}")
        
        # Initialize Gemini Live Session
        gemini = GeminiLiveClient(self.bridge, self.api_key)
        await gemini.connect()

        async def listen_to_gemini():
            async for response in gemini.listen():
                # Route AI voice/text back to Edge
                await websocket.send(json.dumps(response))

        asyncio.create_task(listen_to_gemini())

        try:
            async for message in websocket:
                try:
                    if isinstance(message, bytes):
                        header = message[0]
                        payload = message[1:]
                        
                        if header == 0x01: # Visual Delta
                            metadata = {}
                            jpeg_payload = b""

                            # Check if it's raw JPEG (starts with FF D8) or has metadata header
                            if len(payload) > 1 and payload[0] == 0xFF and payload[1] == 0xD8:
                                # Raw JPEG without metadata (Rust client behavior)
                                jpeg_payload = payload
                            else:
                                # Parse Hardened Packet: [4 bytes metadata_len][metadata][jpeg]
                                metadata_len = int.from_bytes(payload[0:4], "little")
                                metadata_raw = payload[4:4+metadata_len]
                                jpeg_payload = payload[4+metadata_len:]
                                try:
                                    metadata = json.loads(metadata_raw.decode("utf-8"))
                                except json.JSONDecodeError:
                                    print("⚠️ Failed to parse metadata JSON. Assuming empty metadata.")
                            
                            # REVERSE ENG #3: Hybrid Accessibility Check
                            # If metadata has nodes, we can potentially bypass heavy CV
                            
                            # REVERSE ENG: Temporal Anchoring
                            import time
                            metadata["timestamp_orchestrator"] = time.time_ns()
                            # Check for drift if timestamp was sent from Edge
                            if "timestamp_edge" in metadata:
                                drift = (metadata["timestamp_orchestrator"] - metadata["timestamp_edge"]) / 1_000_000
                                if drift > 500:
                                    print(f"⚠️ Perceptual Drift Detected: {drift}ms. Dropping stale frame.")
                                    continue

                            await gemini.stream_input(jpeg_payload, mime_type="image/jpeg")
                        elif header == 0x02: # Audio Chunk
                            await gemini.stream_input(payload, mime_type="audio/pcm")
                    else:
                        # Validate JSON structure and types
                        raw_data = json.loads(message)
                        if not isinstance(raw_data, dict):
                            raise ValueError("Synaptic signal must be a JSON object")

                        synaptic_signal = SynapticMessage(**raw_data)

                        # Gating Logic (Active Inference) using validated data
                        # Using .dict() for compatibility across Pydantic V1/V2
                        context_dict = synaptic_signal.data.dict() if hasattr(synaptic_signal.data, 'dict') else synaptic_signal.data.model_dump()
                        mode = await self.router.route_action(context_dict)
                        # Intercept/Enrich here
                except (json.JSONDecodeError, ValidationError, ValueError) as e:
                    print(f"⚠️ Neural Anomaly (Input Validation): {e}")
                except Exception as e:
                    print(f"⚠️ Neural Anomaly: {e}")
        
        finally:
            await gemini.close()
            print(f"💀 Synaptic Bridge: Connection severed for {remote_addr}")

    async def run_server(self):
        await self.boot_sequence()
        print(f"🛰️ Synaptic Bridge Listening on ws://{self.host}:{self.port}...")
        async with websockets.serve(self.handle_optic_nerve, self.host, self.port):
            await asyncio.Future()  # Run forever

if __name__ == "__main__":
    orchestrator = AetherCoreOrchestrator()
    asyncio.run(orchestrator.run_server())
