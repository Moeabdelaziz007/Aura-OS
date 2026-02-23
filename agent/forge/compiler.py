"""
Aether Forge - Nano-Agent Compiler
Uses Gemini to synthesize ephemeral Python agents for specific tasks.
"""

import os
import re
import json
import logging
import textwrap
from typing import Optional, Dict, Any
from dataclasses import dataclass

try:
    import google.generativeai as genai
except ImportError:
    genai = None

logger = logging.getLogger("AetherCompiler")

@dataclass
class CompiledAgent:
    code: str
    entry_point: str = "execute"
    dependencies: list[str] = None

class NanoAgentCompiler:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if self.api_key and genai:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        else:
            self.model = None
            logger.warning("NanoAgentCompiler: GEMINI_API_KEY missing or google-generativeai not installed. Compiler disabled.")

    async def compile(self, intent: str, context: Dict[str, Any]) -> CompiledAgent:
        """
        Compiles a Nano-Agent (Python function) to handle the given intent.
        """
        if not self.model:
            raise RuntimeError("Compiler unavailable: No API key or library.")

        logger.info(f"🧪 Synthesizing Nano-Agent for: '{intent}'")

        prompt = f"""
        You are the Aether Forge Compiler. Your job is to write a self-contained Python function to execute a specific task.

        TASK: {intent}
        CONTEXT: {json.dumps(context)}

        REQUIREMENTS:
        1. The code must be valid Python 3.
        2. It must define a main async function named `execute(params: dict) -> dict`.
        3. The function must return a dictionary with the results.
        4. Use `httpx` for HTTP requests (it is available in the environment).
        5. Handle exceptions gracefully and return an error dict if something fails.
        6. Do NOT use any external libraries other than `httpx`, `json`, `asyncio`, `re`, `datetime`, `math`.
        7. Return ONLY the code block, no markdown formatting (or use ```python blocks).

        EXAMPLE:
        import httpx
        import asyncio

        async def execute(params):
            url = "https://api.example.com/data"
            async with httpx.AsyncClient() as client:
                resp = await client.get(url)
                return {{"status": resp.status_code, "data": resp.json()}}
        """

        try:
            # We use generate_content_async if available, else synchronous
            # The library might only support sync or await depending on version
            # For safety, we wrap in try/except or just use the sync version in a thread if needed
            # But creating a thread for every compile is okay.
            # actually genai.GenerativeModel.generate_content_async exists in newer versions

            response = await self.model.generate_content_async(prompt)
            raw_code = response.text

            # Extract code from markdown blocks if present
            code = self._extract_code(raw_code)

            return CompiledAgent(code=code)

        except Exception as e:
            logger.error(f"Compilation failed: {e}")
            raise

    async def compile_variants(self, intent: str, context: Dict[str, Any], n: int = 3) -> list[CompiledAgent]:
        """Compiles multiple variants of the agent for consensus."""
        # Simple parallel compilation
        # In a real system, we might vary the temperature or prompt slightly
        tasks = [self.compile(intent, context) for _ in range(n)]
        return await asyncio.gather(*tasks, return_exceptions=True)

    def _extract_code(self, text: str) -> str:
        """Extracts code from markdown code blocks."""
        pattern = r"```python\s*(.*?)\s*```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1)

        # specific fallback for 'python' tag without newline
        pattern_simple = r"```\s*(.*?)\s*```"
        match_simple = re.search(pattern_simple, text, re.DOTALL)
        if match_simple:
            return match_simple.group(1)

        return text
