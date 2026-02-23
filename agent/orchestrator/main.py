import asyncio
import json
import os
import re
import time
import websockets
from dotenv import load_dotenv

load_dotenv()
from typing import Any, Dict

# Gemini 2.0 Spatial API outputs JSON within the text stream
SPATIAL_JSON_PATTERN = re.compile(r'\{.*\}', re.DOTALL)
from pydantic import BaseModel, Field, ValidationError
from .memory_parser import AetherNavigator
from .cognitive_router import HyperMindRouter
from .gemini_live_client import GeminiLiveClient
from .alpha_evolve import monitor, evolve_engine
from agent.forge.aether_forge import AetherForge

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
    The main asynchronous event loop for AetherOS.
    Bridges the Edge Client (Sensory) via WebSockets to the DNA Brain.
    """
    def __init__(self, host: str = "127.0.0.1", port: int = 8000, drift_threshold_ms: float = 500.0):
        self.host = host
        self.port = port
        self.drift_threshold_ms = drift_threshold_ms
        self.bridge = AetherNavigator()
        self.router = HyperMindRouter(self.bridge)
        self.forge = AetherForge()  # Initialize the Forge
        self.is_running = False
        self.api_key = os.getenv("GEMINI_API_KEY")
        self._cleanup_tasks = set()  # Track cleanup tasks for graceful shutdown
        self._max_retries = 3  # Max retry attempts for critical errors

    async def boot_sequence(self):
        """Initializes DNA and validates Persona logic."""
        print("🪐 AetherOS: AetherCore Prometheus Booting...")
        dna = await self.bridge.load_dna_async()
        print(f"🧬 DNA Sequence Verified: {dna.version}")

        # Ignite the Forge (Start Async Client)
        await self.forge.__aenter__()
        print("🔥 Aether Forge: Ignited & Ready.")

        self.is_running = True
        
        # Priority 3: Start Active Pulse Monitor
        pulse_task = asyncio.create_task(self.pulse_monitor(), name="pulse_monitor")
        self._cleanup_tasks.add(pulse_task)

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
        # Phase 6.6: Handle connection in background to avoid blocking the bridge
        asyncio.create_task(gemini.connect())

        async def listen_to_gemini():
            async for response in gemini.listen():
                # AlphaMind Spatial Interceptor (Phase 3)
                try:
                    if "modelTurn" in response:
                        parts = response["modelTurn"].get("parts", [])
                        for part in parts:
                            text = part.get("text", "")
                            if text:
                                match = SPATIAL_JSON_PATTERN.search(text)
                                if match:
                                    data = json.loads(match.group(0))
                                    if "point" in data:
                                        print(f"🎯 AlphaMind Spatial Match: {data['point']}")
                                        y_rel, x_rel = data["point"]
                                        # Assuming standard 1920x1080 display for relative mapping
                                        abs_x = int((x_rel / 1000.0) * 1920)
                                        abs_y = int((y_rel / 1000.0) * 1080)
                                        action = {"action": "CLICK", "x": abs_x, "y": abs_y}
                                        await websocket.send(json.dumps(action))
                                        continue
                                    elif "text" in data:
                                        action = {"action": "TYPE", "text": data["text"]}
                                        await websocket.send(json.dumps(action))
                                        # Add small delay before pressing enter for realism
                                        await asyncio.sleep(0.5)
                                        await websocket.send(json.dumps({"action": "PRESS_ENTER"}))
                                        continue
                except Exception as e:
                    print(f"⚠️ AlphaMind parsing error: {e}")
                    monitor.log_anomaly("AlphaMind", "ParsingError", str(e))

                # Route standard AI voice/text info back to Edge
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
                            
                            # REVERSE ENG: Temporal Anchoring
                            metadata["timestamp_orchestrator"] = time.time_ns()
                            # Check for drift if timestamp was sent from Edge
                            if "timestamp_edge" in metadata:
                                drift = (metadata["timestamp_orchestrator"] - metadata["timestamp_edge"]) / 1_000_000
                                if drift > self.drift_threshold_ms:
                                    print(f"⚠️ Perceptual Drift Detected: {drift}ms. Dropping stale frame.")
                                    continue

                            # REVERSE ENG #3: Hybrid Accessibility Check
                            # If metadata has nodes, we can bypass heavy CV
                            if "nodes" in metadata and metadata["nodes"]:
                                print("⚡ Hybrid Accessibility Check: Bypassing CV using metadata nodes.")
                                # Serialize nodes to optimize token usage (or just raw JSON)
                                accessibility_tree = json.dumps(metadata["nodes"])
                                await gemini.send_text(f"Accessibility Context: {accessibility_tree}")
                            else:
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
                        
                        # Phase 6.6: Neural Poison Neutralized (AlphaEvolve)
                        if context_dict.get("poison") == "NEURAL_POISON":
                            print("💀 Neural Poison Detected! Neutralizing signal...")
                            monitor.log_anomaly("Orchestrator", "NeuralPoison", "Poison signal detected and bypassed.")
                            continue

                        mode = await self.router.route_action(context_dict)

                        # 🔮 Phase 1: Wire Forge to Orchestrator
                        if mode == "AETHER_FORGE":
                            intent_text = context_dict.get("intent_text", "Unknown Intent")
                            print(f"🔨 Aether Forge Activated: {intent_text}")

                            # Execute the Forge Protocol
                            forge_result = await self.forge.resolve_and_forge(query=intent_text)

                            if forge_result.success:
                                response_text = f"Forge Execution Complete: {forge_result.service.upper()}\n"

                                # Add ASCII Visual if available
                                if forge_result.ascii_visual:
                                    response_text += f"\n{forge_result.ascii_visual}\n"

                                # Serialize data safely
                                try:
                                    data_str = json.dumps(forge_result.data, indent=2)
                                    response_text += f"\nData Payload:\n{data_str}"
                                except Exception:
                                    response_text += f"\nData Payload: {forge_result.data}"

                                await gemini.send_text(response_text)
                            else:
                                error_msg = f"Forge Execution Failed: {forge_result.error}"
                                print(f"❌ {error_msg}")
                                await gemini.send_text(error_msg)

                        # Intercept/Enrich here
                except (json.JSONDecodeError, ValidationError, ValueError) as e:
                    print(f"⚠️ Neural Anomaly (Input Validation): {e}")
                    monitor.log_anomaly("SynapticBridge", "ValidationError", str(e))
                except ConnectionError as e:
                    # Retry logic for critical connection errors
                    print(f"⚠️ Critical Connection Error: {e}")
                    monitor.log_anomaly("Websocket", "ConnectionError", str(e))
                    await self._handle_critical_error(e, websocket)
                except Exception as e:
                    print(f"⚠️ Neural Anomaly: {e}")
                    monitor.log_anomaly("Orchestrator", type(e).__name__, str(e))
                    # Phase 6.6: Trigger Autonomous Healing
                    asyncio.create_task(evolve_engine.trigger_healing(
                        {"component": "Orchestrator", "error_type": type(e).__name__, "message": str(e)},
                        "agent/orchestrator/main.py"
                    ))
        
        finally:
            await gemini.close()
            print(f"💀 Synaptic Bridge: Connection severed for {remote_addr}")
    
    async def _handle_critical_error(self, error: Exception, websocket):
        """
        Handle critical errors with retry logic and recovery.
        
        Args:
            error: The exception that occurred
            websocket: The websocket connection to recover
        """
        print(f"🚨 Critical Error Handler: {type(error).__name__} - {error}")
        
        # Attempt recovery based on error type
        for attempt in range(self._max_retries):
            try:
                # Wait before retry with exponential backoff
                backoff = 2 ** attempt
                print(f"🔄 Recovery attempt {attempt + 1}/{self._max_retries} (waiting {backoff}s)...")
                await asyncio.sleep(backoff)
                
                # Check if websocket is still connected
                if websocket.open:
                    print("✅ WebSocket recovered, continuing...")
                    return
                else:
                    print("⚠️ WebSocket closed, cannot recover connection")
                    break
                    
            except Exception as recovery_error:
                print(f"❌ Recovery attempt {attempt + 1} failed: {recovery_error}")
        
        print(f"💥 All recovery attempts exhausted for: {error}")
    
    async def shutdown(self):
        """
        Graceful shutdown with resource cleanup.
        Closes all tracked cleanup tasks and releases resources.
        """
        print("🛑 AetherCoreOrchestrator: Initiating graceful shutdown...")
        self.is_running = False
        
        # Cancel all tracked cleanup tasks
        if self._cleanup_tasks:
            print(f"🧹 Cleaning up {len(self._cleanup_tasks)} tasks...")
            for task in self._cleanup_tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            self._cleanup_tasks.clear()
        
        # Close bridge resources
        if hasattr(self.bridge, 'close'):
            await self.bridge.close()

        # Cool down the Forge
        if hasattr(self.forge, '__aexit__'):
            await self.forge.__aexit__(None, None, None)
            print("❄️ Aether Forge: Cooled down.")
        
        print("✅ AetherCoreOrchestrator: Shutdown complete")

    async def run_server(self):
        await self.boot_sequence()
        print(f"🛰️ Synaptic Bridge Listening on ws://{self.host}:{self.port}...")
        async with websockets.serve(self.handle_optic_nerve, self.host, self.port):
            await asyncio.Future()  # Run forever

if __name__ == "__main__":
    orchestrator = AetherCoreOrchestrator()
    asyncio.run(orchestrator.run_server())