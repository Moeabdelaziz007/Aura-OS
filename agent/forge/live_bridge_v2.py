"""
🌌 AetherOS — Sensory Cortex (Gemini Live Bridge v2.0)
======================================================
Official Google GenAI Live API integration for real-time bi-directional
audio and visual streaming. 
"""

import asyncio
import base64
import io
import logging
import os
from typing import Optional, List

import google.genai as genai
from google.genai import types

from .aether_forge import AetherForge
from .constraint_solver import ConstraintSolver, build_time_context
from .models import VoiceFeatures, ScreenContext
from .stream_utils import AudioStreamer, VisionStreamer
from .motor_cortex import MotorCortex, get_tool_declarations

logger = logging.getLogger("aether.sensory")

class GeminiLiveBridgeV2:
    """The fluid Sensory Cortex of AetherOS."""

    def __init__(self, api_key: Optional[str] = None, forge: Optional[AetherForge] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.forge = forge or AetherForge()
        self.solver = ConstraintSolver()
        self.motor = MotorCortex(forge=self.forge)
        self.session = None
        self._running = False
        self._hot_intent_cache = {} # Inverted Bridge Cache

    async def start_session(self):
        """Initialize the bi-direction session."""
        config = types.LiveConfig(
            model="models/gemini-2.0-flash-exp",
            response_modalities=["AUDIO", "TEXT"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Puck") # High-energy persona
                )
            ),
            generation_config=types.GenerationConfig(
                temperature=0.7,
                candidate_count=1
            ),
            tools=get_tool_declarations()
        )

        logger.info("🎭 sensory-orchestrator: Connecting to Gemini Live...")
        try:
            async with self.client.aio.live.connect(model="gemini-2.0-flash-exp", config=config) as session:
                self.session = session
                self._running = True
                
                # Parallel Multimodal Hub
                await asyncio.gather(
                    self._receive_loop(),
                    self._audio_input_loop(),
                    self._vision_input_loop(),
                )
        except Exception as e:
            logger.error(f"❌ Sensory Cortex failure: {e}")
            self._running = False

    async def _receive_loop(self):
        """Processes real-time responses from Gemini."""
        async for response in self.session.receive():
            if response.server_content:
                # Handle Model Turns
                if response.server_content.model_turn:
                    parts = response.server_content.model_turn.parts
                    for part in parts:
                        if part.text:
                            print(f"[🤖 AetherOS]: {part.text}")
                        if part.inline_data: # Audio shard
                            # In a real app, this would be piped to audio output
                            pass

                # Interruption Awareness
                if response.server_content.interrupted:
                    logger.warning("🚫 Interruption detected. Halting playback...")
                    # Local buffer flush logic here

            if response.tool_call:
                # Motor Cortex: Execute local action
                for call in response.tool_call.function_calls:
                    name = call.name
                    args = call.args
                    call_id = call.id
                    
                    result = await self.motor.dispatch(name, args)
                    
                    # Send response back to the stream
                    await self.session.send(
                        input=types.LiveClientToolResponse(
                            function_responses=[
                                types.LiveFunctionResponse(
                                    name=name,
                                    id=call_id,
                                    response=result
                                )
                            ]
                        )
                    )
                    logger.info(f"🦾 Motor Response sent for {name}")

    async def _audio_input_loop(self):
        """Streams real-time microphone data."""
        streamer = AudioStreamer()
        async for chunk in streamer.get_audio_stream():
            if not self._running: break
            await self.send_audio_chunk(chunk)

    async def _vision_input_loop(self):
        """Streams real-time screen captures."""
        streamer = VisionStreamer()
        async for frame in streamer.get_vision_stream():
            if not self._running: break
            await self.send_frame(frame)

    async def send_audio_chunk(self, audio_data: bytes):
        """Sends PCM 16kHz audio to the bridge."""
        if self.session and self._running:
            await self.session.send(input={"data": audio_data, "mime_type": "audio/pcm"}, end_of_turn=False)

    async def send_frame(self, image_data: bytes):
        """Sends a visual frame to the bridge."""
        if self.session and self._running:
            # 1. Predictive Inverted Bridge: Warm up the state before model asks
            asyncio.create_task(self._predict_and_warmup(image_data))
            
            await self.session.send(input={"data": image_data, "mime_type": "image/jpeg"}, end_of_turn=False)

    async def _predict_and_warmup(self, frame_data: bytes):
        """Analyze visual focus to pre-fetch context from CloudNexus."""
        # conceptual implementation of Inverted Bridge / Predictive Pre-fetching
        # 1. Analyze metadata (mocked focus area)
        focus_area = "browser_settings_pane"  # Simulated visual recognition
        
        if focus_area not in self._hot_intent_cache:
            logger.info(f"🔮 Inverted Bridge: Predictive focus detected on [{focus_area}]. Pre-fetching DNA...")
            # Pre-fetch relevant state from Firestore via Forge
            dna = await self.forge.nexus.get_agent_context(f"intent-{focus_area}")
            self._hot_intent_cache[focus_area] = dna
            logger.info(f"✨ Inverted Bridge: Context for [{focus_area}] is WARM.")

    async def stop(self):
        self._running = False
        if self.session:
            await self.session.close()
            logger.info("🎭 Sensory Cortex: Session closed.")

async def demo_sensory_bridge():
    """Connectivity verification."""
    bridge = GeminiLiveBridgeV2()
    # This is a passive verification for the implementation logic
    print("✨ Sensory Cortex v2.0 logic initialized.")
    # Real testing requires streaming input which is part of Phase 4
    
if __name__ == "__main__":
    asyncio.run(demo_sensory_bridge())
