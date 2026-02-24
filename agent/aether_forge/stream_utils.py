"""
🌌 AetherOS — Stream Utilities
==============================
Handles low-level audio PCM conversion and screen capture frames. 
Designed for zero-latency multimodal input.
"""

import asyncio
import io
import time
import logging
from typing import AsyncGenerator

try:
    import pyaudio
except ImportError:
    pyaudio = None

logger = logging.getLogger("aether.streams")

class AetherAudioStreamer:
    """PCM 16kHz Mono Streamer."""
    
    def __init__(self, sample_rate=16000, chunk_size=512):
        self.rate = sample_rate
        self.chunk = chunk_size
        self.p = pyaudio.PyAudio() if pyaudio else None
        self.stream = None

    async def get_audio_stream(self) -> AsyncGenerator[bytes, None]:
        """Generator for real-time PCM bytes."""
        if not self.p:
            logger.warning("⚠️ PyAudio not found. Streaming silence (Simulator).")
            while True:
                await asyncio.sleep(0.03) # ~30ms chunks
                yield b'\x00' * (self.chunk * 2)
            return

        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )
        
        try:
            while True:
                # Non-blocking read simulation
                data = self.stream.read(self.chunk, exception_on_overflow=False)
                yield data
                await asyncio.sleep(0) # Yield control
        finally:
            self.stream.stop_stream()
            self.stream.close()

class AetherVisionStreamer:
    """Real-time Screen Capture for Intent Collapse."""

    async def get_vision_stream(self) -> AsyncGenerator[bytes, None]:
        """Generator for JPEG frames."""
        try:
            import mss
            from PIL import Image
        except ImportError:
            logger.warning("⚠️ mss/pillow not found. Visual simulator active.")
            while True:
                await asyncio.sleep(1.0)
                yield b"FAKE_JPEG_SENSE"
            return

        with mss.mss() as sct:
            # Monitor 1 capture
            monitor = sct.monitors[1]
            while True:
                # Capture screen -> PIL Image -> JPEG Bytes
                sct_img = sct.grab(monitor)
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                
                # Resize for multimodal efficiency (Gemini prefers specific scales)
                img.thumbnail((1024, 1024))
                
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG', quality=85)
                yield img_byte_arr.getvalue()
                
                await asyncio.sleep(1.0) # 1 FPS is optimal for intent observation

def pcm_to_wav_header(pcm_data: bytes, sample_rate: int = 16000) -> bytes:
    """Helper to wrap raw PCM in WAV for certain playback engines."""
    import struct
    header = struct.pack('<4sI4s4sIHHIIHH4sI',
        b'RIFF', 36 + len(pcm_data), b'WAVE', b'fmt ', 16, 1, 1, 
        sample_rate, sample_rate * 2, 2, 16, b'data', len(pcm_data))
    return header + pcm_data
