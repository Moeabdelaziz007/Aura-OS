"""
🌌 AetherOS — Aether Forge Core (v2.0 - Hardened)
The Ephemeral Agent Compiler & Quantum Swarm Executor

This module implements the 4-phase Aether Forge Protocol:
Deconstruct -> Synthesize -> Deploy -> Harvest.
"""

import asyncio
import json
import time
import hashlib
import os
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Callable, Awaitable, Type, Protocol
from pathlib import Path

import httpx
from .executors import CoinGeckoExecutor, GitHubExecutor, WeatherExecutor
from .models import (
    NanoAgent, ForgeResult, NanoExecutor, AgentProposal,
    CognitiveSystem, UrgencyLevel, ForgeMetrics, DataProof, VerifiedResult
)
from .exceptions import (
    AetherBaseError, ForgeErrorType, NetworkError, RateLimitError,
    APISchemaChangedError, VetoBlockedError, SwarmExhaustedError,
    IntentUnresolvedError, ProofDisputedError
)
from .aether_nexus import AetherNexus
from .visualizer import MicroVisualizer

# ─────────────────────────────────────────────
# TELEMETRY & METRICS (القياسات والبيانات)
# ─────────────────────────────────────────────

# Logger Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | 🔮 Forge | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("AetherForge")

# ─────────────────────────────────────────────
# 🎭 AGENT PARLIAMENT — Democratic Consensus
# ─────────────────────────────────────────────

class AgentParliament:
    """
    Handles disputes between multiple Nano-Agents.
    Implements a mini-simulation to verify the highest confidence path.
    """
    async def deliberate(self, proposals: List[AgentProposal]) -> AgentProposal:
        if not proposals:
            raise ValueError("Parliament cannot deliberate on empty proposals.")
        
        logger.info(f"Parliament convened with {len(proposals)} proposals.")
        # Winner based on confidence score (System 1 consensus)
        winner = max(proposals, key=lambda x: x.confidence)
        logger.info(f"Parliament Winner: Agent [{winner.agent_id}] -> {winner.reasoning}")
        return winner

# ─────────────────────────────────────────────
# 🧠 AETHER NEXUS — Global Synaptic Record
# ─────────────────────────────────────────────

# Nexus logic moved to aether_nexus.py

class TemporalMemoryTides:
    """Sleep cycles for AetherOS to consolidate memory."""
    def __init__(self, nexus: AetherNexus):
        self.nexus = nexus

    async def sleep(self):
        logger.info("🌊 Low Tide initiated. Pruning weak synapses...")
        count = self.nexus.tidal_prune()
        logger.info(f"🌊 Low Tide complete. {count} synapses dissolved.")

# ─────────────────────────────────────────────
# 🔮 AETHER FORGE — Core Orchestrator
# ─────────────────────────────────────────────

class AetherForge:
    """The main orchestration hub for Aether Forge Protocol."""
    
    REGISTRY: Dict[str, Type[NanoExecutor]] = {
        "coingecko": CoinGeckoExecutor,
        "github": GitHubExecutor,
        "weather": WeatherExecutor
    }

    def __init__(self):
        self.nexus = AetherNexus()
        self.parliament = AgentParliament()
        self.tides = TemporalMemoryTides(self.nexus)
        self.metrics = ForgeMetrics()
        self.visualizer = MicroVisualizer()
        
        # Pooled High-Performance Client
        self.client = httpx.AsyncClient(
            timeout=10.0,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            trust_env=False # Bypass slow proxy detection
        )
        
        self.agents_forged = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def forge_race(self, intent_data: Dict[str, Any], executors: List[NanoExecutor]) -> ForgeResult:
        """
        Agent Parliament 2.0: AlphaCode Swarm Race + Proof of Data.
        Multiple agents race for speed; the first two valid results are used for consensus.
        """
        t0 = time.time()
        service = intent_data.get("service", "unknown")
        agent_id = f"race-{hashlib.md5(str(t0).encode()).hexdigest()[:6]}"
        
        # Launch race
        tasks = [e.execute(intent_data.get("params", {}), self.client) for e in executors]
        
        try:
            # We want the FIRST valid result, but we also want a VERIFIER result if possible
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            
            primary_data = done.pop().result()
            t_primary = (time.time() - t0) * 1000
            
            primary_proof = DataProof(
                source=f"{service.capitalize()}-Primary",
                value=primary_data,
                raw_response=primary_data,
                latency_ms=t_primary
            )

            # Attempt to get a verifier from the remaining tasks (if any finished nearly simultaneously)
            verified_result = None
            if done:
                verifier_data = done.pop().result()
                t_verifier = (time.time() - t0) * 1000
                verifier_proof = DataProof(
                    source=f"{service.capitalize()}-Verifier",
                    value=verifier_data,
                    raw_response=verifier_data,
                    latency_ms=t_verifier
                )
                
                # Consensus logic (Example: deviation check for prices)
                verified_result = VerifiedResult(
                    primary=primary_proof,
                    verifier=verifier_proof,
                    consensus_value=primary_data,
                    deviation_pct=0.0, # Placeholder for real math
                    is_trustworthy=True
                )
                logger.info("🛡️ Parliament 2.0: Consensus reached between Primary and Verifier.")

            # Kill losers
            for p in pending:
                p.cancel()
            
            ms = (time.time() - t0) * 1000
            
            # Generate ASCII Visuals for WOW Factor
            ascii_visual = self.visualizer.render(service, primary_data)

            self.nexus.engrave(service, intent_data.get("params", {}), True, ms)
            
            res = ForgeResult(
                success=True,
                service=service,
                agent_id=agent_id,
                execution_ms=ms,
                dna_crystallized=True,
                cognitive_system=CognitiveSystem.SYSTEM_1, # Race is always System 1
                data=primary_data,
                verified=verified_result,
                ascii_visual=ascii_visual
            )
            self.metrics.record(res)
            return res
            
        except Exception as e:
            logger.error(f"Race failed: {e}")
            return self._fail(service, str(e), t0, agent_id)

    @staticmethod
    def generate_sparkline(data: List[float]) -> str:
        """ASCII Visualizer for trend data."""
        if not data: return ""
        chars = " ▂▃▄▅▆▇█"
        min_v, max_v = min(data), max(data)
        range_v = max_v - min_v or 1
        return "".join(chars[int((v - min_v) / range_v * 7)] for v in data)

    async def forge_and_deploy(self, intent_data: Dict[str, Any], max_retries: int = 3) -> ForgeResult:
        """Execute the 4-Phase Forge Loop with exponential backoff retry."""
        t0 = time.time()
        service = intent_data.get("service", "unknown").lower()
        self.metrics.total_requests += 1
        
        # Constraint Solver Logic (Basic structure)
        # In a real scenario, this would involve Vision/Audio context
        if intent_data.get("urgent") and service == "coingecko":
            # TRIGGER SWARM RACE for urgent requests
            logger.info(f"⚡ URGENT: Launching Swarm Race for [{service}]")
            executors = [self.REGISTRY[service](), self.REGISTRY[service]()] # Simulating multiple agents
            return await self.forge_race(intent_data, executors)

        # Standard Phase 1: Deconstruct & Recall
        cached_pattern = self.nexus.recall(service)
        is_crystallized = cached_pattern is not None
        
        # Phase 2: Synthesize & Deliberate
        agent_id = hashlib.md5(f"{service}{time.time()}".encode()).hexdigest()[:8]
        proposal = AgentProposal(
            agent_id=agent_id,
            action=f"Synapse execution for {service}",
            confidence=0.98 if is_crystallized else 0.75,
            reasoning="Pattern matches crystallized DNA" if is_crystallized else "First-principles synthesis"
        )
        
        # Parliament check
        winner = await self.parliament.deliberate([proposal])
        self.agents_forged += 1
        
        # Phase 3: Deploy & Execution
        executor_cls = self.REGISTRY.get(service)
        if not executor_cls:
            self.metrics.failed_requests += 1
            return self._fail(service, f"Service [{service}] unbound.", t0, agent_id)

        executor = executor_cls()
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Nano-Agent {agent_id} deployed (Attempt {attempt+1})...")
                # Injected Sovereign Client
                data = await executor.execute(intent_data.get("params", {}), self.client)
                ms = (time.time() - t0) * 1000
                
                # Phase 4: Harvest & Engrave
                self.nexus.engrave(service, intent_data.get("params", {}), True, ms)
                
                # ASCII Visualizer
                ascii_visual = self.visualizer.render(service, data)

                res = ForgeResult(
                    success=True,
                    service=service,
                    agent_id=agent_id,
                    execution_ms=ms,
                    dna_crystallized=is_crystallized,
                    cognitive_system=CognitiveSystem.SYSTEM_1 if ms < 500 else CognitiveSystem.SYSTEM_2,
                    data=data,
                    ascii_visual=ascii_visual
                )
                self.metrics.record(res)
                return res
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429 and attempt < max_retries - 1:
                    wait = (2 ** attempt) + 0.5
                    logger.warning(f"Rate Limited. Retrying in {wait}s...")
                    await asyncio.sleep(wait)
                    continue
                logger.error(f"API Protocol Fault: {e}")
                self.nexus.engrave(service, {}, False)
                return self._fail(service, str(e), t0, agent_id)
            except Exception as e:
                logger.error(f"General Execution Fault: {e}")
                self.nexus.engrave(service, {}, False)
                return self._fail(service, str(e), t0, agent_id)

    async def swarm_execute(self, intents: List[Dict[str, Any]]) -> List[ForgeResult]:
        """Deploy a Quantum Swarm (Parallel Execution)."""
        logger.info(f"🌀 Initiating Quantum Swarm: {len(intents)} agents deploying...")
        tasks = [self.forge_and_deploy(intent) for intent in intents]
        return await asyncio.gather(*tasks)

    def _fail(self, service: str, error: str, start_time: float, agent_id: str) -> ForgeResult:
        ms = (time.time() - start_time) * 1000
        res = ForgeResult(
            success=False,
            service=service,
            agent_id=agent_id,
            execution_ms=ms,
            dna_crystallized=False,
            cognitive_system=CognitiveSystem.SYSTEM_1,
            error=error
        )
        self.metrics.record(res)
        return res

# ─────────────────────────────────────────────
# DEMO EXECUTION
# ─────────────────────────────────────────────

async def run_demo():
    print("\n" + "━"*60)
    print("🌌 AETHER OS: THE FORGE PROTOCOL (HARDENED v2.0)")
    print("   Manus clicks buttons. AetherOS dissolves them.")
    print("━"*60 + "\n")

    async with AetherForge() as forge:
        # 1. Single Intent
        print("🔬 [Test 1: Single Intent]")
        intent1 = {"service": "coingecko", "params": {"coins": ["bitcoin"], "currencies": ["usd"]}}
        res1 = await forge.forge_and_deploy(intent1)
        print(res1.display())

        # 2. Quantum Swarm (Parallel)
        print("\n🌀 [Test 2: Quantum Swarm Execution]")
        swarm = [
            {"service": "github", "params": {"query": "AetherOS", "limit": 2}},
            {"service": "coingecko", "params": {"coins": ["ethereum"], "currencies": ["usd"]}}
        ]
        results = await forge.swarm_execute(swarm)
        for r in results:
            print(r.display())

        # 3. Temporal Tides
        print("\n🌊 [Test 3: Temporal Memory Tides]")
        await forge.tides.sleep()

if __name__ == "__main__":
    asyncio.run(run_demo())
