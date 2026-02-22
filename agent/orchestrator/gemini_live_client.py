import asyncio
import json
import os
import base64
from typing import Any, Dict, Optional, AsyncGenerator

# Optional websockets import; allow repository tools to run without it
try:
    import websockets  # type: ignore
except Exception:  # pragma: no cover
    websockets = None  # type: ignore

from .memory_parser import AuraNavigator

class GeminiLiveClient:
    """
    The Multimodal Soul of AuraOS.
    Handles real-time BidiGenerateContent streams with Gemini 3.1 Pro.
    """
    def __init__(self, bridge: AuraNavigator, api_key: str):
        self.bridge = bridge
        self.api_key = api_key
        self.url = f"wss://generativelanguage.googleapis.com/ws/google.genai.v1alpha.GenerativeService.BidiGenerateContent?key={self.api_key}"
        self.ws = None
        self.is_ready = False

    async def connect(self):
        """Establishes connection and performs the Setup Protocol with retry and optional encryption."""
        if not self.api_key:
            raise ValueError("GeminiLiveClient requires GEMINI_API_KEY environment variable")

        print("🚀 Gemini Live: Connecting to Multimodal Webhook...")
        # loop until connection succeeds (simple backoff)
        while True:
            try:
                self.ws = await websockets.connect(self.url, ping_interval=20, ping_timeout=10)
                break
            except Exception as e:
                print(f"❌ Gemini Live: connection failed ({e}), retrying in 5s...")
                await asyncio.sleep(5)
        
        # 1. Load DNA and Skills for Setup
        dna = await self.bridge.load_dna_async()
        
        # 2. Construct Setup Message
        setup_msg = {
            "setup": {
                "model": "models/gemini-1.5-pro-002",
                "generation_config": {
                    "response_modalities": ["AUDIO", "TEXT"],
                    "speech_config": {
                        "voice_config": {"prebuilt_voice_config": {"voice_name": "Aoide"}}
                    }
                },
                "system_instruction": {
                    "role": "system",
                    "parts": [{"text": json.dumps(dna.soul)}]
                }
            }
        }
        
        await self.ws.send(json.dumps(setup_msg))
        
        # Wait for setup_complete
        while True:
            response = await self.ws.recv()
            if "setupComplete" in response:
                print("✅ Gemini Live: Setup Complete. Spark of Life Ignited.")
                self.is_ready = True
                break
            # keep reading until success or break

    async def stream_input(self, data: bytes, mime_type: str = "image/jpeg"):
        """Pumps sensory data into the Live API."""
        if not self.is_ready: return

        # Format as realtimeInput
        input_msg = {
            "realtime_input": {
                "media_chunks": [{
                    "mime_type": mime_type,
                    "data": base64.b64encode(data).decode("utf-8")
                }]
            }
        }
        await self.ws.send(json.dumps(input_msg))

    async def listen(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Listens for AI responses and function calls and enriches them with nexus context."""
        if self.ws is None:
            return

        async for message in self.ws:
            try:
                payload = json.loads(message)
            except Exception:
                # invalid JSON, skip
                continue
            
            if "serverContent" in payload:
                # pre‑route context: find similar nexus nodes
                try:
                    hits = await self.bridge.search_nexus(payload["serverContent"])
                    payload["serverContent"]["nexus_hits"] = hits
                except Exception:
                    pass
                yield payload["serverContent"]
            
            if "toolCall" in payload:
                try:
                    hits = await self.bridge.search_nexus(payload["toolCall"])
                    payload["toolCall"]["nexus_hits"] = hits
                except Exception:
                    pass
                # This will be routed through the HyperMindRouter for VFE check
                yield payload["toolCall"]

    async def close(self):
        if self.ws:
            await self.ws.close()
