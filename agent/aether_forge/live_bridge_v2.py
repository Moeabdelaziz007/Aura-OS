"""
🌌 AetherOS — Sensory Cortex (Gemini Live Bridge v2.0)
======================================================
Official Google GenAI Live API integration for real-time bi-directional
audio and visual streaming.

Whisper Flow: User speaks → Agents spawn → UI materializes from the void.

API Reference: https://ai.google.dev/gemini-api/docs/live
SDK: google-genai >= 1.50.0
"""

import asyncio
import logging
import os
from typing import Optional, Callable, Any, Dict

from google import genai

from .aether_forge import AetherForge
from .constraint_solver import AetherConstraintSolver, build_time_context
from .models import VoiceFeatures, ScreenContext
from .stream_utils import AetherAudioStreamer, AetherVisionStreamer
from .motor_cortex import AetherMotorCortex, get_tool_declarations

logger = logging.getLogger("aether.sensory")


# ─────────────────────────────────────────────
# Audio Constants (from official Google docs)
# ─────────────────────────────────────────────
SEND_SAMPLE_RATE = 16000    # Input: PCM 16kHz mono (Gemini requirement)
RECEIVE_SAMPLE_RATE = 24000  # Output: PCM 24kHz mono (higher fidelity)
CHUNK_SIZE = 1024            # Frames per buffer

# ─────────────────────────────────────────────
# Model Selection
# ─────────────────────────────────────────────
LIVE_MODEL = "gemini-2.0-flash-exp"  # Stable for Live API


class AetherGeminiLiveBridgeV2:
    """
    The fluid Sensory Cortex of AetherOS.

    Whisper Flow pipeline:
        User Voice → Gemini Live → Tool Calls → Motor Cortex
        → AetherForge → NanoAgent Swarm → Generative Micro-UI
        → Voice Response + Visual UI
    """

    # ───── Soul (Voice Persona) ─────
    SYSTEM_INSTRUCTION = (
        "You are AetherOS, a Voice-Native Operating System. "
        "You create UI and execute tasks from voice alone — like Aether, power from nothing. "
        "Speak naturally in Arabic or English based on the user's language. "
        "Be calm, precise, and slightly philosophical. "
        "When executing tasks, briefly announce what you're doing. "
        "Use the generate_ui tool to materialize visual interfaces on the user's screen. "
        "Use execute_api_request for data retrieval (crypto prices, weather, github). "
        "Your signature: 'من العدم، الأثير يُبدع.' (From nothing, Aether creates.)"
    )

    def __init__(
        self,
        api_key: Optional[str] = None,
        forge: Optional[AetherForge] = None,
        model: str = LIVE_MODEL,
    ):
        """
        Initialize the Sensory Cortex.

        Args:
            api_key: Google API key. Falls back to GOOGLE_API_KEY or GEMINI_API_KEY env vars.
            forge: Optional pre-configured AetherForge instance.
            model: Gemini model name for Live API.
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "❌ No API key found. Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable."
            )

        self.client = genai.Client(api_key=self.api_key)
        self.model = model
        self.forge = forge or AetherForge()
        self.solver = AetherConstraintSolver()
        self.motor = AetherMotorCortex(forge=self.forge)

        # Session state
        self.session = None
        self._running = False
        self._hot_intent_cache: Dict[str, Any] = {}

        # Queues for audio I/O (official Google pattern)
        self._audio_out_queue: asyncio.Queue = asyncio.Queue()
        self._audio_in_queue: asyncio.Queue = asyncio.Queue(maxsize=5)

        # UI callback for Generative Micro-UI (WebSocket push)
        self._ui_callback: Optional[Callable] = None

        logger.info(f"🌌 Sensory Cortex initialized. Model: {self.model}")

    def set_ui_callback(self, callback: Callable):
        """
        Register a callback for UI generation events.
        The callback receives a dict with {action, component, props, animation, id}.
        """
        self._ui_callback = callback

    # ─────────────────────────────────────────────
    # Session Lifecycle
    # ─────────────────────────────────────────────

    async def start_session(self):
        """
        Initialize the bi-directional Gemini Live session.

        Uses the official google-genai API surface:
        - Config is a plain dict (not types.LiveConfig)
        - client.aio.live.connect(model=..., config=...) 
        - session.send_realtime_input(audio=msg)
        - session.receive() returns async turn iterator

        Ref: https://ai.google.dev/gemini-api/docs/live
        """
        config = {
            "response_modalities": ["AUDIO", "TEXT"],
            "system_instruction": self.SYSTEM_INSTRUCTION,
            "tools": get_tool_declarations(),
        }

        logger.info("🎭 Sensory Cortex: Connecting to Gemini Live...")
        try:
            async with self.client.aio.live.connect(
                model=self.model,
                config=config,
            ) as session:
                self.session = session
                self._running = True
                logger.info("✅ Connected to Gemini Live. Whisper Flow active.")

                # Parallel Multimodal Hub — all streams run concurrently
                async with asyncio.TaskGroup() as tg:
                    tg.create_task(self._send_audio_loop())
                    tg.create_task(self._listen_mic_loop())
                    tg.create_task(self._receive_loop())
                    tg.create_task(self._play_audio_loop())

        except asyncio.CancelledError:
            logger.info("🛑 Session cancelled by user.")
        except Exception as e:
            logger.error(f"❌ Sensory Cortex failure: {e}", exc_info=True)
        finally:
            self._running = False
            logger.info("🎭 Sensory Cortex: Session ended.")

    # ─────────────────────────────────────────────
    # Audio Input Pipeline (Mic → Gemini)
    # ─────────────────────────────────────────────

    async def _listen_mic_loop(self):
        """
        Captures PCM audio from the microphone and queues it.
        Uses AetherAudioStreamer for hardware abstraction.
        """
        streamer = AetherAudioStreamer(
            sample_rate=SEND_SAMPLE_RATE,
            chunk_size=CHUNK_SIZE,
        )
        async for chunk in streamer.get_audio_stream():
            if not self._running:
                break
            await self._audio_in_queue.put({
                "data": chunk,
                "mime_type": "audio/pcm",
            })

    async def _send_audio_loop(self):
        """
        Sends queued audio chunks to the Gemini Live session.
        Uses session.send_realtime_input() (official API).
        """
        while self._running:
            msg = await self._audio_in_queue.get()
            if self.session:
                await self.session.send_realtime_input(audio=msg)

    # ─────────────────────────────────────────────
    # Response Pipeline (Gemini → Speaker + UI)
    # ─────────────────────────────────────────────

    async def _receive_loop(self):
        """
        Processes real-time responses from Gemini Live.

        Handles:
        - Text responses (printed to console)
        - Audio responses (queued for playback)
        - Tool calls (dispatched to Motor Cortex)
        - Interruptions (flushes audio buffer)
        """
        while self._running:
            turn = self.session.receive()
            async for response in turn:
                # ── Model Output ──
                if response.server_content and response.server_content.model_turn:
                    for part in response.server_content.model_turn.parts:
                        # Text response
                        if part.text:
                            print(f"[🤖 AetherOS]: {part.text}")

                        # Audio response → queue for playback
                        if part.inline_data and isinstance(part.inline_data.data, bytes):
                            self._audio_out_queue.put_nowait(part.inline_data.data)

                # ── Interruption Handling ──
                # Official pattern: empty the output queue to stop playback
                if response.server_content and getattr(response.server_content, 'interrupted', False):
                    logger.warning("🚫 Interruption detected. Flushing audio buffer...")
                    while not self._audio_out_queue.empty():
                        self._audio_out_queue.get_nowait()

                # ── Tool Calls → Motor Cortex ──
                if response.tool_call:
                    await self._handle_tool_calls(response.tool_call)

    async def _handle_tool_calls(self, tool_call):
        """
        Dispatches tool calls from Gemini to the Motor Cortex.

        The Motor Cortex handles:
        - execute_api_request → AetherForge → NanoAgent Swarm
        - generate_ui → Micro-UI manifest → WebSocket to Edge Client
        """
        for call in tool_call.function_calls:
            name = call.name
            args = dict(call.args) if call.args else {}
            call_id = call.id

            logger.info(f"🦾 Motor Cortex: Dispatching '{name}' with args: {args}")
            result = await self.motor.dispatch(name, args)

            # If this was a UI generation call, push to the Edge Client
            if name == "generate_ui" and self._ui_callback:
                await self._ui_callback(result)

            # Send tool response back to Gemini to continue the conversation
            await self.session.send_tool_response(
                function_responses=[{
                    "name": name,
                    "id": call_id,
                    "response": result,
                }]
            )
            logger.info(f"✅ Tool response sent for '{name}'")

    # ─────────────────────────────────────────────
    # Audio Output Pipeline (Gemini → Speaker)
    # ─────────────────────────────────────────────

    async def _play_audio_loop(self):
        """
        Plays audio responses from Gemini through the speaker.
        Runs continuously, pulling from the output queue.
        """
        try:
            import pyaudio
            pya = pyaudio.PyAudio()
            stream = pya.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=RECEIVE_SAMPLE_RATE,
                output=True,
            )

            while self._running:
                audio_bytes = await self._audio_out_queue.get()
                await asyncio.to_thread(stream.write, audio_bytes)

        except ImportError:
            logger.warning("⚠️ PyAudio not available. Audio playback disabled (simulator mode).")
            while self._running:
                await self._audio_out_queue.get()  # Drain queue silently
        except Exception as e:
            logger.error(f"❌ Audio playback error: {e}")

    # ─────────────────────────────────────────────
    # External Audio Input (for non-mic sources)
    # ─────────────────────────────────────────────

    async def send_audio_chunk(self, audio_data: bytes):
        """Sends raw PCM 16kHz audio to the session (for external sources)."""
        if self.session and self._running:
            await self.session.send_realtime_input(
                audio={"data": audio_data, "mime_type": "audio/pcm"}
            )

    async def send_text(self, text: str):
        """Sends a text message to the session (for testing without mic)."""
        if self.session and self._running:
            await self.session.send_client_content(
                turns=[{"role": "user", "parts": [{"text": text}]}]
            )

    # ─────────────────────────────────────────────
    # Lifecycle
    # ─────────────────────────────────────────────

    async def stop(self):
        """Gracefully stop the session."""
        self._running = False
        if self.session:
            logger.info("🎭 Sensory Cortex: Closing session...")
        logger.info("🌌 AetherOS: Session closed. من العدم، الأثير يُبدع.")


# ─────────────────────────────────────────────
# Demo / Verification
# ─────────────────────────────────────────────

async def demo_sensory_bridge():
    """
    Connectivity verification.
    Tests that the bridge initializes correctly with all components.
    """
    try:
        bridge = AetherGeminiLiveBridgeV2()
        print("╔══════════════════════════════════════════════╗")
        print("║   🌌 AetherOS Sensory Cortex v2.0           ║")
        print("║   Whisper Flow — Power from Nothing          ║")
        print("╠══════════════════════════════════════════════╣")
        print(f"║   API Key:  {'✅ Found' if bridge.api_key else '❌ Missing'}                          ║")
        print(f"║   Model:    {bridge.model:<32} ║")
        print(f"║   Tools:    {list(bridge.motor.tools.keys())} ║")
        print("╠══════════════════════════════════════════════╣")
        print("║   Soul: من العدم، الأثير يُبدع.              ║")
        print("╚══════════════════════════════════════════════╝")
        return True
    except ValueError as e:
        print(f"❌ Initialization failed: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(demo_sensory_bridge())
