"""
🌌 AetherOS — Aether Forge Core (v2.1.0)
Pillar: Prometheus / QuantumWeaver
Role: The Ephemeral Agent Compiler & Executor

"Manus clicks buttons. AetherOS dissolves them."
"""

import asyncio
import json
import time
import hashlib
import httpx
import os
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, Type
from pathlib import Path

# Setup Clinical Logging (Interface Dissolver Voice)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | 🔮 Forge | %(levelname)s | %(message)s")
logger = logging.getLogger("AetherForge")

# ─────────────────────────────────────────────
from .executors import CoinGeckoExecutor, GitHubExecutor, WeatherExecutor

# ─────────────────────────────────────────────
# 🧬 CORE PROTOCOLS & DATA STRUCTURES
# ─────────────────────────────────────────────
# ... (rest of code) ...

class AetherForge:
    """The main orchestration hub for Aether Forge Protocol."""
    
    REGISTRY: Dict[str, Type[NanoExecutor]] = {
        "coingecko": CoinGeckoExecutor,
        "github": GitHubExecutor,
        "weather": WeatherExecutor
    }
    
    # Static Templates for MVP (Mock Archaeology)
    TEMPLATES = {
        "coingecko": {"base": "https://api.coingecko.com/api/v3", "auth": None},
        "github": {"base": "https://api.github.com", "auth": "Bearer"},
        "weather": {"base": "https://api.openweathermap.org", "auth": "API_KEY"}
    }

    def __init__(self):
        self.nexus = AetherNexus()
        self.stats = {"forged": 0, "ms_saved": 0}

    def _deconstruct(self, intent: str) -> tuple[str, Dict[str, Any]]:
        """Deconstruct intent into Service + Params. Uses logical keyword matching (MVP)."""
        intent = intent.lower()
        if any(w in intent for w in ["price", "bitcoin", "crypto", "eth"]):
            coins = []
            if "btc" in intent or "bitcoin" in intent: coins.append("bitcoin")
            if "eth" in intent or "ethereum" in intent: coins.append("ethereum")
            if not coins: coins = ["bitcoin", "ethereum", "solana"]
            return "coingecko", {"coins": coins}
        
        if any(w in intent for w in ["github", "repo", "code"]):
            return "github", {"query": intent.replace("github", "").strip()}
            
        return "coingecko", {"coins": ["bitcoin"]}

    async def forge(self, intent: str) -> ForgeResult:
        start_time = time.time()
        logger.info(f"Synthesizing Nano-Agent for intent: '{intent}'")
        
        # 1. Deconstruction
        service_name, params = self._deconstruct(intent)
        
        # 2. Nexus Recall (System 1)
        pattern = self.nexus.recall(service_name) or self.TEMPLATES.get(service_name)
        
        if not pattern:
            return ForgeResult(False, None, service_name, 0, "null", False, "Service pattern unavailable.")

        # 3. Agent Synthesis
        agent_id = hashlib.md5(f"{intent}{time.time()}".encode()).hexdigest()[:8]
        agent = NanoAgent(id=agent_id, intent=intent, service=service_name, params=params)
        self.stats["forged"] += 1
        
        # 4. Deployment & Execution
        executor_cls = self.REGISTRY.get(service_name)
        if not executor_cls:
            return ForgeResult(False, None, service_name, 0, agent_id, False, f"No executor registered for {service_name}")
        
        executor = executor_cls()
        try:
            data = await executor.execute(params)
            success = True
            error = None
        except Exception as e:
            logger.error(f"Execution Failure [Agent #{agent_id}]: {e}")
            data = None
            success = False
            error = str(e)

        ms_latency = (time.time() - start_time) * 1000
        
        # 5. Harvesting & Crystallization
        self.nexus.engrave(service_name, pattern, success)
        
        if success:
            self.stats["ms_saved"] += max(0, 15000 - ms_latency) # Baseline vs 15s UI navigation

        logger.info(f"Agent #{agent_id} dissolved. Latency: {ms_latency:.2f}ms. Total Forge Savings: {self.stats['ms_saved']/1000:.1f}s")
        
        return ForgeResult(
            success=success,
            data=data,
            service=service_name,
            execution_ms=ms_latency,
            agent_id=agent_id,
            dna_crystallized=success,
            error=error
        )

# ─────────────────────────────────────────────
# 🧪 DEMO SUITE
# ─────────────────────────────────────────────

async def demo():
    forge = AetherForge()
    print("\n" + " ✨ " * 15)
    print("      AETHER OS: FORGE PROTOCOL DEMO")
    print(" ✨ " * 15)

    # Test Case 1: Crypto
    res = await forge.forge("Check Bitcoin and Ethereum prices")
    print(res.display())

    await asyncio.sleep(1)

    # Test Case 2: GitHub
    res = await forge.forge("Find AetherOS on github")
    print(res.display())

    # Test Case 3: System 1 Trigger
    print("\n[Triggering System 1 Recall]")
    res = await forge.forge("BTC price update")
    print(res.display())

if __name__ == "__main__":
    asyncio.run(demo())
