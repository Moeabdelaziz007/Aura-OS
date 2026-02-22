import asyncio
import json
import base64
from typing import Any, Dict, AsyncGenerator

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
    MAX_RETRIES = 5
    RETRY_DELAY = 5  # Base delay in seconds for exponential backoff
    
    def __init__(self, bridge: AuraNavigator, api_key: str):
        self.bridge = bridge
        self.api_key = api_key
        self.url = "wss://generativelanguage.googleapis.com/ws/google.genai.v1alpha.GenerativeService.BidiGenerateContent"
        self.ws = None
        self.is_ready = False

    async def connect(self):
        """Establishes connection and performs the Setup Protocol with retry and optional encryption."""
        if not self.api_key:
            raise ValueError("GeminiLiveClient requires GEMINI_API_KEY environment variable")

        print("🚀 Gemini Live: Connecting to Multimodal Webhook...")
        # Retry loop with exponential backoff
        for attempt in range(self.MAX_RETRIES):
            try:
                self.ws = await websockets.connect(
                    self.url,
                    ping_interval=20,
                    ping_timeout=10,
                    extra_headers={"x-goog-api-key": self.api_key}
                )
                print(f"✅ Gemini Live: Connection established on attempt {attempt + 1}")
                break
            except Exception as e:
                if attempt == self.MAX_RETRIES - 1:
                    # Max retries exceeded
                    error_msg = f"Gemini Live: Connection failed after {self.MAX_RETRIES} attempts. Last error: {e}"
                    print(f"❌ {error_msg}")
                    raise ConnectionError(error_msg) from e
                
                # Calculate exponential backoff delay
                backoff_delay = self.RETRY_DELAY * (2 ** attempt)
                print(f"❌ Gemini Live: Connection failed (attempt {attempt + 1}/{self.MAX_RETRIES}): {e}")
                print(f"🔄 Retrying in {backoff_delay}s...")
                await asyncio.sleep(backoff_delay)
        
        if not self.ws:
            raise ConnectionError("Gemini Live Circuit Breaker Triggered: Max retries exceeded.")
        
        # 1. Load DNA and Skills for Setup
        dna = await self.bridge.load_dna_async()
        
        # 2. Construct Setup Message
        spatial_instruction = (
            "You are AuraOS, an AI Agent controlling a user's computer. "
            "You can see the screen. To click on an element, respond with the exact coordinates "
            "in the JSON format: {\"point\": [y, x]} where y and x are integers between 0 and 1000 "
            "representing relative screen coordinates (y is top-to-bottom, x is left-to-right). "
            "To type text, respond with {\"text\": \"your_text_here\"}."
        )

        setup_msg = {
            "setup": {
                "model": "models/gemini-2.0-flash-exp",
                "generation_config": {
                    "response_modalities": ["AUDIO", "TEXT"],
                    "speech_config": {
                        "voice_config": {"prebuilt_voice_config": {"voice_name": "Aoide"}}
                    }
                },
                "system_instruction": {
                    "role": "system",
                    "parts": [
                        {"text": json.dumps(dna.soul)},
                        {"text": spatial_instruction}
                    ]
                }
            }
        }
        
        await self.ws.send(json.dumps(setup_msg))
        
        # Wait for setup_complete with Timeout Constraint
        try:
            async def wait_for_setup():
                while True:
                    response = await self.ws.recv()
                    if "setupComplete" in response:
                        print("✅ Gemini Live: Setup Complete. Spark of Life Ignited.")
                        self.is_ready = True
                        break
            
            await asyncio.wait_for(wait_for_setup(), timeout=10.0)
        except asyncio.TimeoutError:
            print("❌ Gemini Live: Setup Complete handshake timed out.")
            await self.close()
            raise ConnectionError("Setup handshake timed out. Zombie connection prevented.")

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
