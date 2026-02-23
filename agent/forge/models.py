"""
AetherOS Core Models
====================
Enterprise-grade data models with full type safety.
Every dataclass is immutable where possible, validated on creation.
"""

from __future__ import annotations

import uuid
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Protocol

import httpx
import asyncio
from agent.core.telemetry import TelemetryManager

# ─────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────

class CognitiveSystem(Enum):
    """Dual-process cognitive model."""
    SYSTEM_1 = auto()   # Reflexive — instant (<150ms)
    SYSTEM_2 = auto()   # Reflective — deep reasoning


class UrgencyLevel(Enum):
    """Acoustic urgency tiers derived from voice analysis."""
    CRITICAL  = 1   # τ ≤ 0.2  — panic, act NOW
    HIGH      = 2   # τ ≤ 0.4  — stressed
    MEDIUM    = 3   # τ ≤ 0.6  — normal
    LOW       = 4   # τ ≤ 0.8  — calm
    MINIMAL   = 5   # τ ≤ 1.0  — relaxed, explain everything


class ServiceStatus(Enum):
    """Executor health states."""
    HEALTHY   = auto()
    DEGRADED  = auto()
    DEAD      = auto()


class VetoDecision(Enum):
    """SOUL constitutional veto outcomes."""
    APPROVED             = auto()
    BLOCKED              = auto()
    REQUIRES_CONFIRMATION = auto()


# ─────────────────────────────────────────────
# Voice & Vision Context
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class VoiceFeatures:
    """Extracted acoustic features from Gemini Live audio stream."""
    speech_rate_wpm: float          # Words per minute
    pitch_variance: float           # 0.0 (monotone) → 1.0 (high variance)
    volume_db: float                # Decibels
    pause_frequency: float          # Pauses per minute
    transcript: str                 # Raw transcription
    language: str = "ar"           # Detected language
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def urgency_score(self) -> float:
        """
        Composite urgency score 0.0 → 1.0.
        High score = more urgent = lower τ threshold.
        """
        rate_score    = min(self.speech_rate_wpm / 250.0, 1.0)
        pitch_score   = self.pitch_variance
        volume_score  = min(max((self.volume_db + 20) / 40.0, 0.0), 1.0)
        pause_penalty = max(1.0 - self.pause_frequency / 20.0, 0.0)
        return (rate_score * 0.4 + pitch_score * 0.35 +
                volume_score * 0.15 + pause_penalty * 0.1)


@dataclass(frozen=True)
class ScreenContext:
    """What Gemini Vision sees on the user's screen."""
    raw_description: str
    detected_assets: List[str]      # ["SOL", "BTC", "ETH"]
    detected_app: str               # "Binance", "TradingView", etc.
    detected_numbers: List[float]   # Price values visible on screen
    screenshot_b64: Optional[str] = None
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class TimeContext:
    """Temporal signals that constrain intent."""
    hour: int
    is_market_hours: bool
    day_of_week: int                # 0=Monday
    is_weekend: bool
    market_session: str             # "pre", "open", "after", "closed"
    timestamp: datetime = field(default_factory=datetime.utcnow)


# ─────────────────────────────────────────────
# Intent & Constraints
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class ResolvedIntent:
    """
    A partial user query + 4 constraints → 1 deterministic intent.
    Inspired by AlphaFold: constraints collapse ambiguity.
    """
    raw_query: str
    action: str                     # "price_check", "github_search", "weather"
    target: str                     # "SOL", "bitcoin", "Cairo"
    urgency: UrgencyLevel
    cognitive_system: CognitiveSystem
    tau: float                      # Dynamic threshold 0.0 → 1.0
    confidence: float               # 0.0 → 1.0
    reasoning: str                  # Why this intent was chosen
    timestamp: datetime = field(default_factory=datetime.utcnow)
    intent_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])


# ─────────────────────────────────────────────
# Nano-Agent & Execution
# ─────────────────────────────────────────────

@dataclass
class NanoAgent:
    """
    An ephemeral micro-agent compiled for a single task.
    Born → Executes → Dies. TTL enforced strictly.
    """
    id: str                         = field(default_factory=lambda: str(uuid.uuid4())[:8])
    intent: str                     = ""
    service: str                    = ""
    params: Dict[str, Any]          = field(default_factory=dict)
    created_at: datetime            = field(default_factory=datetime.utcnow)
    ttl_seconds: int                = 30
    energy_cost: float              = 1.0

    @property
    def is_alive(self) -> bool:
        age = (datetime.utcnow() - self.created_at).total_seconds()
        return age < self.ttl_seconds

    @property
    def age_ms(self) -> float:
        return (datetime.utcnow() - self.created_at).total_seconds() * 1000


@dataclass
class DataProof:
    """
    Proof of Data from a single source.
    Agent Parliament 2.0: results must be verified by 2 sources.
    """
    source: str
    value: Any
    raw_response: Dict[str, Any]
    latency_ms: float
    fetched_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class VerifiedResult:
    """
    A result verified by ≥2 independent sources.
    Consensus check before presenting to user.
    """
    primary: DataProof
    verifier: DataProof
    consensus_value: Any
    deviation_pct: float            # % difference between sources
    is_trustworthy: bool            # deviation < threshold
    warning: Optional[str] = None


@dataclass
class ForgeResult:
    """
    The final output of a complete Aether Forge cycle.
    Rich result with timing, DNA state, and visualization.
    """
    success: bool
    service: str
    agent_id: str
    execution_ms: float
    dna_crystallized: bool
    cognitive_system: CognitiveSystem
    data: Optional[Dict[str, Any]]          = None
    verified: Optional[VerifiedResult]      = None
    ascii_visual: Optional[str]             = None   # ASCII chart
    error: Optional[str]                    = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def display(self) -> str:
        """Rich terminal output for demo."""
        status = "✅ DISSOLVED" if self.success else "❌ FAILED"
        sys_label = "⚡ System 1 (Instant)" if self.cognitive_system == CognitiveSystem.SYSTEM_1 \
                    else "🧠 System 2 (Deep)"
        dna_label = "🧬 Crystallized (fast path)" if self.dna_crystallized \
                    else "🔬 Synthesized (learning)"

        lines = [
            "",
            "━" * 52,
            f"  🌌 AETHER FORGE — {status}",
            "━" * 52,
            f"  🎯 Service     : {self.service.upper()}",
            f"  ⚡ Speed       : {self.execution_ms:.0f}ms",
            f"  🧠 Cognition   : {sys_label}",
            f"  {dna_label}",
        ]

        if self.verified:
            v = self.verified
            trust = "✅ Trusted" if v.is_trustworthy else "⚠️  Disputed"
            lines += [
                f"  🔍 Verified    : {trust} ({v.deviation_pct:.1f}% deviation)",
                f"  📡 Sources     : {v.primary.source} + {v.verifier.source}",
            ]

        if self.error:
            lines.append(f"  💥 Error       : {self.error}")

        if self.ascii_visual:
            lines.append("")
            lines.append(self.ascii_visual)

        lines.append("━" * 52)
        return "\n".join(lines)


# ─────────────────────────────────────────────
# Memory & DNA
# ─────────────────────────────────────────────

@dataclass
class DNAPattern:
    """
    A crystallized execution pattern stored in AetherNexus.
    Survives via Digital Darwinism — low energy = pruned.
    """
    service: str
    params_template: Dict[str, Any]
    avg_latency_ms: float
    success_rate: float
    energy_credits: float
    use_count: int                  = 0
    last_used: datetime             = field(default_factory=datetime.utcnow)
    created_at: datetime            = field(default_factory=datetime.utcnow)

    def is_viable(self) -> bool:
        return self.energy_credits > 0.0 and self.success_rate > 0.1


# ─────────────────────────────────────────────
# Metrics & Telemetry
# ─────────────────────────────────────────────

@dataclass
class ForgeMetrics:
    """Live telemetry — updated after every forge cycle."""
    total_requests: int     = 0
    successful: int         = 0
    failed: int             = 0
    cache_hits: int         = 0
    total_latency_ms: float = 0.0
    swarm_races: int        = 0
    veto_blocks: int        = 0

    @property
    def success_rate(self) -> float:
        return self.successful / max(self.total_requests, 1)

    @property
    def avg_latency_ms(self) -> float:
        return self.total_latency_ms / max(self.total_requests, 1)

    @property
    def cache_hit_rate(self) -> float:
        return self.cache_hits / max(self.total_requests, 1)

    def record(self, result: ForgeResult) -> None:
        self.total_requests += 1
        self.total_latency_ms += result.execution_ms
        if result.success:
            self.successful += 1
        else:
            self.failed += 1

        # 📡 Live Telemetry Update
        telemetry_data = {
            "total_requests": self.total_requests,
            "successful_forges": self.successful,
            "failed_forges": self.failed,
            "avg_latency_ms": self.avg_latency_ms,
            "last_active": datetime.utcnow().isoformat(),
            "current_state": "Executing (System 2)" if result.cognitive_system == CognitiveSystem.SYSTEM_2 else "Reflexive (System 1)"
        }
        asyncio.create_task(TelemetryManager.update(telemetry_data))

    def summary(self) -> str:
        return (
            f"📊 Metrics | "
            f"Requests: {self.total_requests} | "
            f"Success: {self.success_rate:.0%} | "
            f"Avg: {self.avg_latency_ms:.0f}ms | "
            f"Cache: {self.cache_hit_rate:.0%}"
        )

@dataclass
class AgentProposal:
    """A proposal for action from a Nano-Agent for deliberation."""
    agent_id: str
    action: str
    confidence: float
    reasoning: str

class NanoExecutor(Protocol):
    """Protocol for API-native executors (The Synaptic Bonds)."""
    async def execute(self, params: Dict[str, Any], client: httpx.AsyncClient) -> Dict[str, Any]:
        ...
