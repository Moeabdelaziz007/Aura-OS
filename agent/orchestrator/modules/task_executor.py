"""
Task Executor Module

Handles task execution and websocket handling logic for the AetherOS orchestrator.

Classes:
    TaskExecutor: Manages task execution and websocket message handling
"""

import asyncio
import json
import time
import re
from typing import TYPE_CHECKING, Callable, Any, Dict

if TYPE_CHECKING:
    from ..memory_parser import AetherNavigator
    from ..cognitive_router import HyperMindRouter
    from ..gemini_live_client import GeminiLiveClient
    from agent.forge.aether_forge import AetherForge
    from agent.forge.constraint_solver import MemorySignal
    from agent.forge.models import ForgeResult


# Gemini 2.0 Spatial API outputs JSON within the text stream
SPATIAL_JSON_PATTERN = re.compile(r'\{.*\}', re.DOTALL)


class TaskExecutor:
    """
    Manages task execution and websocket message handling.

    Responsible for:
    - Processing real-time binary/JSON synaptic bridge signals
    - Handling visual delta (image) data
    - Handling audio chunk data
    - Processing text/JSON messages
    - Critical error handling with retry logic
    """

    def __init__(
        self,
        bridge: "AetherNavigator",
        router: "HyperMindRouter",
        forge: "AetherForge",
        memory_signal: "MemorySignal",
        drift_threshold_ms: float = 500.0,
        max_retries: int = 3
    ):
        """
        Initialize the Task Executor.

        Args:
            bridge: The AetherNavigator for memory operations
            router: The HyperMindRouter for action routing
            forge: The AetherForge for task execution
            memory_signal: The MemorySignal for short-term session memory
            drift_threshold_ms: Threshold for detecting perceptual drift in milliseconds
            max_retries: Maximum retry attempts for critical errors
        """
        self.bridge = bridge
        self.router = router
        self.forge = forge
        self.memory_signal = memory_signal
        self.drift_threshold_ms = drift_threshold_ms
        self._max_retries = max_retries

    async def handle_optic_nerve(
        self,
        websocket: Any,
        gemini_client: "GeminiLiveClient",
        update_memory_callback: Callable[["ForgeResult"], None],
        log_anomaly_callback: Callable[[str, str, str], None],
        trigger_healing_callback: Callable[[Dict[str, str], str], None]
    ) -> None:
        """
        Process real-time binary/JSON synaptic bridge signals.

        Handles incoming websocket messages including:
        - Visual delta (0x01): Image data with metadata
        - Audio chunk (0x02): Audio PCM data
        - JSON messages: Text and action commands

        Args:
            websocket: The websocket connection
            gemini_client: The Gemini Live client for streaming
            update_memory_callback: Callback to update memory with forge results
            log_anomaly_callback: Callback to log anomalies
            trigger_healing_callback: Callback to trigger autonomous healing
        """
        remote_addr = websocket.remote_address
        print(f"🛰️ Synaptic Bridge: Connection established from {remote_addr}")

        # Start listening to Gemini in background
        asyncio.create_task(self._listen_to_gemini(websocket, gemini_client))

        try:
            async for message in websocket:
                try:
                    if isinstance(message, bytes):
                        await self._handle_binary_message(
                            message, websocket, gemini_client
                        )
                    else:
                        await self._handle_json_message(
                            message, websocket, gemini_client,
                            update_memory_callback, log_anomaly_callback,
                            trigger_healing_callback
                        )
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"⚠️ Neural Anomaly (Input Validation): {e}")
                    log_anomaly_callback("SynapticBridge", "ValidationError", str(e))
                except ConnectionError as e:
                    print(f"⚠️ Critical Connection Error: {e}")
                    log_anomaly_callback("Websocket", "ConnectionError", str(e))
                    await self._handle_critical_error(e, websocket)
                except Exception as e:
                    print(f"⚠️ Neural Anomaly: {e}")
                    log_anomaly_callback("Orchestrator", type(e).__name__, str(e))
                    # Trigger Autonomous Healing
                    asyncio.create_task(trigger_healing_callback(
                        {"component": "Orchestrator", "error_type": type(e).__name__, "message": str(e)},
                        "agent/orchestrator/main.py"
                    ))
        finally:
            await gemini_client.close()
            print(f"💀 Synaptic Bridge: Connection severed for {remote_addr}")

    async def _listen_to_gemini(
        self,
        websocket: Any,
        gemini_client: "GeminiLiveClient"
    ) -> None:
        """
        Listen to Gemini Live responses and route them appropriately.

        Args:
            websocket: The websocket connection to send responses to
            gemini_client: The Gemini Live client to listen to
        """
        async for response in gemini_client.listen():
            # AlphaMind Spatial Interceptor
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

            # Route standard AI voice/text info back to Edge
            await websocket.send(json.dumps(response))

    async def _handle_binary_message(
        self,
        message: bytes,
        websocket: Any,
        gemini_client: "GeminiLiveClient"
    ) -> None:
        """
        Handle binary messages from the websocket.

        Args:
            message: The binary message
            websocket: The websocket connection
            gemini_client: The Gemini Live client
        """
        header = message[0]
        payload = message[1:]

        if header == 0x01:  # Visual Delta
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
                    return

            # REVERSE ENG #3: Hybrid Accessibility Check
            # If metadata has nodes, we can bypass heavy CV
            if "nodes" in metadata and metadata["nodes"]:
                print("⚡ Hybrid Accessibility Check: Bypassing CV using metadata nodes.")
                # Serialize nodes to optimize token usage (or just raw JSON)
                accessibility_tree = json.dumps(metadata["nodes"])
                await gemini_client.send_text(f"Accessibility Context: {accessibility_tree}")
            else:
                await gemini_client.stream_input(jpeg_payload, mime_type="image/jpeg")

        elif header == 0x02:  # Audio Chunk
            await gemini_client.stream_input(payload, mime_type="audio/pcm")

    async def _handle_json_message(
        self,
        message: str,
        websocket: Any,
        gemini_client: "GeminiLiveClient",
        update_memory_callback: Callable[["ForgeResult"], None],
        log_anomaly_callback: Callable[[str, str, str], None],
        trigger_healing_callback: Callable[[Dict[str, str], str], None]
    ) -> None:
        """
        Handle JSON messages from the websocket.

        Args:
            message: The JSON message as string
            websocket: The websocket connection
            gemini_client: The Gemini Live client
            update_memory_callback: Callback to update memory
            log_anomaly_callback: Callback to log anomalies
            trigger_healing_callback: Callback to trigger healing
        """
        # Import here to avoid circular dependency
        from ..main import SynapticMessage

        raw_data = json.loads(message)
        if not isinstance(raw_data, dict):
            raise ValueError("Synaptic signal must be a JSON object")

        synaptic_signal = SynapticMessage(**raw_data)

        # Gating Logic (Active Inference) using validated data
        context_dict = synaptic_signal.data.dict() if hasattr(synaptic_signal.data, 'dict') else synaptic_signal.data.model_dump()

        # Phase 6.6: Neural Poison Neutralized
        if context_dict.get("poison") == "NEURAL_POISON":
            print("💀 Neural Poison Detected! Neutralizing signal...")
            log_anomaly_callback("Orchestrator", "NeuralPoison", "Poison signal detected and bypassed.")
            return

        mode = await self.router.route_action(context_dict)

        # 🔮 Phase 1: Wire Forge to Orchestrator
        if mode == "AETHER_FORGE":
            intent_text = context_dict.get("intent_text", "Unknown Intent")
            print(f"🔨 Aether Forge Activated: {intent_text}")

            # Execute the Forge Protocol, passing Memory Signal
            forge_result = await self.forge.resolve_and_forge(
                query=intent_text,
                memory=self.memory_signal
            )

            if forge_result.success:
                # Update Memory Signal
                update_memory_callback(forge_result)

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

                await gemini_client.send_text(response_text)
            else:
                error_msg = f"Forge Execution Failed: {forge_result.error}"
                print(f"❌ {error_msg}")
                await gemini_client.send_text(error_msg)

    async def _handle_critical_error(self, error: Exception, websocket: Any) -> None:
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
