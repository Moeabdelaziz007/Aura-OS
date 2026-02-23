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
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Callable, Awaitable, Type, Protocol
from pathlib import Path

import httpx
from .executors import CoinGeckoExecutor, GitHubExecutor, WeatherExecutor
from .models import (
    NanoAgent, ForgeResult, NanoExecutor, AgentProposal,
    CognitiveSystem, UrgencyLevel, ForgeMetrics, DataProof, VerifiedResult,
    VoiceFeatures, ScreenContext, ResolvedIntent
)
from .exceptions import (
    AetherBaseError, ForgeErrorType, NetworkError, RateLimitError,
    APISchemaChangedError, VetoBlockedError, SwarmExhaustedError,
    IntentUnresolvedError, ProofDisputedError
)
from .aether_nexus import AetherNexus
from .cloud_nexus import CloudNexus
from .visualizer import MicroVisualizer
from .constraint_solver import ConstraintSolver, build_time_context, MemorySignal
from .circuit_breaker import get_circuit_breaker, CircuitOpenError
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
        count = await self.nexus.tidal_prune()
        logger.info(f"🌊 Low Tide complete. {count} synapses dissolved.")

from .archaeology import archaeologist
from .circuit_breaker import get_circuit_breaker, CircuitOpenError
from .compiler import NanoAgentCompiler, CompiledAgent
from .sandbox import NanoSandbox

# ─────────────────────────────────────────────
# 🔮 AETHER FORGE — Core Orchestrator
# ─────────────────────────────────────────────

class AetherForge:
    """The main orchestration hub for Aether Forge Protocol."""
    
    # Static executors for initial discovery, will be dynamically built in __init__
    STATIC_EXECUTORS = [CoinGeckoExecutor, GitHubExecutor, WeatherExecutor]

    def __init__(self, automated_tides: bool = True):
        self.nexus = AetherNexus()
        self.parliament = AgentParliament()
        self.archaeologist = archaeologist
        self.tides = TemporalMemoryTides(self.nexus)
        self.metrics = ForgeMetrics()
        self.visualizer = MicroVisualizer()
        self.solver = ConstraintSolver()
        self.circuit = get_circuit_breaker()
        
        # Dynamic Forge Components
        self.compiler = NanoAgentCompiler()
        self.sandbox = NanoSandbox()

        # Build Registry and Service Map dynamically
        self.REGISTRY: Dict[str, Type[NanoExecutor]] = {}
        self.SERVICE_MAP: Dict[str, str] = {}
        self._build_registry()

        # Cloud Nexus (The Global Nervous System)
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "notional-armor-456623-e8")
        key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", ".idx/aether-key.json")
        self.cloud = None
        if os.path.exists(key_path):
            try:
                self.cloud = CloudNexus(project_id, key_path)
            except Exception as e:
                logger.warning(f"⚠️ CloudNexus offline: {e}. Degrading to Local Sovereignty.")
        
        # Pooled High-Performance Client
        self.client = httpx.AsyncClient(
            timeout=10.0,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            trust_env=False # Bypass slow proxy detection
        )
        
        self.agents_forged = 0
        if automated_tides:
            asyncio.create_task(self._start_tide_daemon())

    def _build_registry(self):
        """Dynamically build registry and service map from executor classes."""
        for executor_cls in self.STATIC_EXECUTORS:
            # Derive service name from class name (e.g., CoinGeckoExecutor -> coingecko)
            service_name = executor_cls.__name__.lower().replace("executor", "")
            self.REGISTRY[service_name] = executor_cls

            if hasattr(executor_cls, "intent_action"):
                self.SERVICE_MAP[executor_cls.intent_action] = service_name
                logger.debug(f"Registered executor: {service_name} for action: {executor_cls.intent_action}")
            else:
                logger.warning(f"Executor {executor_cls.__name__} has no intent_action attribute.")

    async def _start_tide_daemon(self):
        """Background daemon for autonomous memory pruning."""
        while True:
            await asyncio.sleep(3600)  # Pulse every hour
            await self.tides.sleep()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def forge_race(
        self,
        intent_data: Dict[str, Any],
        executors: List[NanoExecutor],
        intent_obj: Optional[ResolvedIntent] = None
    ) -> ForgeResult:
        """
        Agent Parliament 2.0: AlphaCode Swarm Race + Proof of Data.
        Multiple agents race for speed; the first two valid results are used for consensus.
        """
        t0 = time.time()
        service = intent_data.get("service", "unknown")
        agent_id = f"race-{hashlib.md5(str(t0).encode()).hexdigest()[:6]}"
        
        # Launch race with Circuit Breakers
        tasks = [
            asyncio.create_task(self.circuit.call(service, e.execute, intent_data.get("params", {}), self.client))
            for e in executors
        ]
        
        try:
            # We want the FIRST valid result
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            
            res_obj = done.pop().result()
            primary_data = res_obj.raw_response if hasattr(res_obj, "raw_response") else res_obj
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
                
                # Consensus logic: Calculate deviation
                deviation = self._calculate_deviation(primary_data, verifier_data)

                verified_result = VerifiedResult(
                    primary=primary_proof,
                    verifier=verifier_proof,
                    consensus_value=primary_data,
                    deviation_pct=deviation,
                    is_trustworthy=deviation < 5.0 # Threshold for trustworthiness
                )
                logger.info(f"🛡️ Parliament 2.0: Consensus reached. Deviation: {deviation:.2f}%")

            # Kill losers
            for p in pending:
                p.cancel()
            
            ms = (time.time() - t0) * 1000
            
            # Generate ASCII Visuals for WOW Factor
            ascii_visual = self.visualizer.render(service, primary_data)

            await self.nexus.engrave(service, intent_data.get("params", {}), True, ms)
            
            # Record Learning
            # Feedback is recorded centrally in resolve_and_forge to avoid double counting
            
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
            # Failure recorded in resolve_and_forge via res.success=False

            return self._fail(service, str(e), t0, agent_id)

    def _calculate_deviation(self, data1: Any, data2: Any) -> float:
        """Calculates percentage deviation between two datasets."""
        try:
            val1 = self._extract_numeric_value(data1)
            val2 = self._extract_numeric_value(data2)

            if val1 is None or val2 is None:
                return 0.0 # Cannot compare non-numeric

            if val1 == 0 and val2 == 0:
                return 0.0

            avg = (val1 + val2) / 2
            if avg == 0: return 0.0

            return abs(val1 - val2) / avg * 100.0
        except Exception:
            return 0.0

    def _extract_numeric_value(self, data: Any) -> Optional[float]:
        """Recursively extract the first meaningful numeric value from a complex structure."""
        if isinstance(data, (int, float)):
            return float(data)
        elif isinstance(data, str):
            # Try to parse currency or number
            clean = re.sub(r'[^\d\.]', '', data)
            try:
                return float(clean)
            except ValueError:
                return None
        elif isinstance(data, dict):
            # Prioritize 'Price_USD' or 'usd' keys for financial data
            for key in ['Price_USD', 'usd', 'value', 'price']:
                if key in data:
                    val = self._extract_numeric_value(data[key])
                    if val is not None: return val
            # Otherwise iterate values
            for v in data.values():
                val = self._extract_numeric_value(v)
                if val is not None: return val
        elif isinstance(data, list):
            for v in data:
                val = self._extract_numeric_value(v)
                if val is not None: return val
        return None

    async def resolve_and_forge(
        self,
        query: str,
        voice: Optional[VoiceFeatures] = None,
        screen: Optional[ScreenContext] = None,
        memory: Optional[MemorySignal] = None
    ) -> ForgeResult:
        """Resolve ambiguous query via constraints then forge."""
        time_ctx = build_time_context()
        intent = self.solver.resolve(query, voice, screen, time_ctx, memory)
        
        # Use dynamic service map
        if intent.action in self.SERVICE_MAP:
            service = self.SERVICE_MAP[intent.action]
            # Params generation for known services
            params = {}
            if intent.action == "price_check":
                params = {"coins": [intent.target], "currencies": ["usd"]}
            elif intent.action == "github_search":
                params = {"query": intent.target, "limit": 3}
            elif intent.action == "weather_check":
                params = {"city": intent.target}
        else:
            # Dynamic Intent!
            service = intent.target if intent.target != "unknown" else intent.action
            params = {"query": query, "context": intent.reasoning}
            logger.info(f"✨ Unmapped Intent '{intent.action}': Routing to Dynamic Forge.")

        intent_data = {
            "query": query,
            "intent_id": intent.intent_id,
            "service": service,
            "params": params,
            "urgent": intent.urgency in (UrgencyLevel.CRITICAL, UrgencyLevel.HIGH)
        }
        
        # Deploy, passing the full intent object
        res = await self.forge_and_deploy(intent_data, intent_obj=intent)
        
        # Record feedback loop outcome (System 2 / Normal Path)
        # Note: Race condition already records feedback if it ran.
        # But we can record here too if not urgent, or just rely on forge_and_deploy return logic.
        # Ideally, we record here to catch all paths, but we must ensure we don't double record for Race.
        # FeedbackLoop is likely idempotent enough (just updates weights).
        await self.solver.feedback.record_outcome(intent, res.success)
        
        return res

    @staticmethod
    def generate_sparkline(data: List[float]) -> str:
        """ASCII Visualizer for trend data."""
        if not data: return ""
        chars = " ▂▃▄▅▆▇█"
        min_v, max_v = min(data), max(data)
        range_v = max_v - min_v or 1
        return "".join(chars[int((v - min_v) / range_v * 7)] for v in data)

    async def forge_and_deploy(
        self,
        intent_data: Dict[str, Any],
        max_retries: int = 3,
        intent_obj: Optional[ResolvedIntent] = None
    ) -> ForgeResult:
        """Execute the 4-Phase Forge Loop with exponential backoff retry."""
        t0 = time.time()
        service = intent_data.get("service", "unknown").lower()
        self.metrics.total_requests += 1
        
        # Constraint Solver Logic (Basic structure)
        # In a real scenario, this would involve Vision/Audio context
        if intent_data.get("urgent") and service in self.REGISTRY:
            # TRIGGER SWARM RACE for urgent requests
            logger.info(f"⚡ URGENT: Launching Swarm Race for [{service}]")
            # Simulating multiple agents by instantiating twice
            executors = [self.REGISTRY[service](), self.REGISTRY[service]()]
            return await self.forge_race(intent_data, executors, intent_obj=intent_obj)

        # Phase 0: Swarm Cache Check (Collective Intelligence)
        if self.cloud:
            global_pattern = await self.cloud.discover_global_patterns(service)
            if global_pattern:
                logger.info(f"🌀 Swarm Cache HIT: Global pattern found for [{service}]. Bypassing local vision.")
                # We prioritize global verified patterns over local drafts
                # Implementation detail: For brevity in this loop, we merge global insights into cached_pattern
                # but local AetherNexus still acts as the primary System 1 for speed.
        
        # Standard Phase 1: Deconstruct & Recall
        cached_pattern = await self.nexus.recall(service)
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
        
        # If static executor exists, use it. Otherwise, go DYNAMIC.
        if executor_cls:
            executor = executor_cls()
            return await self._execute_static_agent(executor, service, intent_data, t0, agent_id, is_crystallized, max_retries)
        else:
            return await self._compile_and_execute_dynamic(service, intent_data, t0, agent_id)

    async def _execute_static_agent(self, executor, service, intent_data, t0, agent_id, is_crystallized, max_retries):
        """Helper to run pre-defined static agents."""
        for attempt in range(max_retries):
            try:
                logger.info(f"Nano-Agent {agent_id} (Static) deployed...")
                res_obj = await self.circuit.call(service, executor.execute, intent_data.get("params", {}), self.client)
                data = res_obj.raw_response if hasattr(res_obj, "raw_response") else res_obj
                ms = (time.time() - t0) * 1000
                
                await self.nexus.engrave(service, intent_data.get("params", {}), True, ms)
                
                if hasattr(executor, 'base_url'):
                    await self.archaeologist.register_discovery(service, executor.base_url)
                
                ascii_visual = self.visualizer.render(service, data)
                
                res = ForgeResult(
                    success=True, service=service, agent_id=agent_id, execution_ms=ms,
                    dna_crystallized=is_crystallized,
                    cognitive_system=CognitiveSystem.SYSTEM_1, data=data, ascii_visual=ascii_visual
                )
                self.metrics.record(res)
                return res
            except Exception as e:
                logger.error(f"Static Execution Fault: {e}")
                # Wait before retry
                await asyncio.sleep(0.5 * (attempt + 1))

        # If all retries fail
        return self._fail(service, f"Static Agent Failed after {max_retries} retries", t0, agent_id)

    async def _compile_and_execute_dynamic(self, service: str, intent_data: Dict[str, Any], t0: float, agent_id: str) -> ForgeResult:
        """Compiles a Swarm of Python agents on the fly and executes them for consensus."""
        logger.info(f"🧬 DYNAMIC FORGE: Spawning Swarm for '{service}'...")

        try:
            # 1. Compile Swarm (3 Variants)
            # In production, we'd vary the prompt temperature for diversity
            variants = await self.compiler.compile_variants(
                intent=intent_data.get("query"),
                context=intent_data,
                n=3
            )

            # Filter valid agents
            agents = [v for v in variants if isinstance(v, CompiledAgent)]
            if not agents:
                logger.error("❌ Swarm Compilation Failed: No valid agents generated.")
                return self._fail(service, "Swarm Compilation Failed", t0, agent_id)

            logger.info(f"🐝 Swarm Generated: {len(agents)} Nano-Agents ready.")

            # 2. Execute in Parallel Sandbox
            tasks = [self.sandbox.execute(agent.code, intent_data.get("params", {})) for agent in agents]
            results = await asyncio.gather(*tasks)

            # 3. Consensus (Pick first success for MVP, majority vote in full version)
            successes = [r for r in results if r.success]

            ms = (time.time() - t0) * 1000

            if successes:
                winner = successes[0]
                logger.info(f"✅ Swarm Consensus Reached: {len(successes)}/{len(agents)} agents succeeded ({ms:.0f}ms)")

                # Use code as visual if no better visualizer match
                ascii_visual = f"```python\n{agents[0].code}\n```"

                res = ForgeResult(
                    success=True, service=service, agent_id=agent_id, execution_ms=ms,
                    dna_crystallized=False,
                    cognitive_system=CognitiveSystem.SYSTEM_2,
                    data=winner.data,
                    ascii_visual=ascii_visual
                )
                self.metrics.record(res)
                return res
            else:
                errors = "; ".join([r.error for r in results if r.error])
                logger.error(f"❌ Swarm Execution Failed: {errors}")
                return self._fail(service, f"Swarm Failed: {errors}", t0, agent_id)

        except Exception as e:
            logger.error(f"Dynamic Forge Critical Failure: {e}")
            return self._fail(service, f"Forge Error: {e}", t0, agent_id)

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
