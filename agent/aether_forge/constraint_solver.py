"""
AetherOS — Constraint Solver (Intent Resolution Engine)
=========================================================
Inspired by Fold-inspired: don't guess from ambiguous language alone.
Let 4 real-world constraints COLLAPSE into one deterministic intent.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from .models import (
    CognitiveSystem,
    ResolvedIntent,
    ScreenContext,
    TimeContext,
    UrgencyLevel,
    VoiceFeatures,
)
import json
from .feedback_loop import AetherFeedbackLoop

logger = logging.getLogger("aether.constraint")

# ─────────────────────────────────────────────
# Tau Calculator — Dynamic Cognitive Threshold
# ─────────────────────────────────────────────

TAU_MIN = 0.05   # Critical urgency → instant System 1
TAU_MAX = 0.95   # Completely calm  → deep System 2

def compute_tau(urgency_score: float) -> Tuple[float, CognitiveSystem]:
    """
    Map urgency score [0.0, 1.0] → tau [TAU_MIN, TAU_MAX]
    High urgency → low tau → System 1 (instant)
    Low urgency  → high tau → System 2 (deep)
    """
    tau = TAU_MAX - (urgency_score * (TAU_MAX - TAU_MIN))
    system = CognitiveSystem.SYSTEM_1 if tau < 0.5 else CognitiveSystem.SYSTEM_2
    return round(tau, 3), system


def classify_urgency(urgency_score: float) -> UrgencyLevel:
    if urgency_score >= 0.85: return UrgencyLevel.CRITICAL
    if urgency_score >= 0.65: return UrgencyLevel.HIGH
    if urgency_score >= 0.45: return UrgencyLevel.MEDIUM
    if urgency_score >= 0.25: return UrgencyLevel.LOW
    return UrgencyLevel.MINIMAL


# ─────────────────────────────────────────────
# Intent Templates
# ─────────────────────────────────────────────

@dataclass
class IntentTemplate:
    """A recognizable intent pattern with keywords and context signals."""
    action: str
    service: str
    keywords_ar: List[str]
    keywords_en: List[str]
    context_signals: List[str]      # What screen/app context matches this
    weight: float = 1.0             # Base confidence weight


INTENT_CATALOG: List[IntentTemplate] = [
    IntentTemplate(
        action="price_check",
        service="coingecko",
        keywords_ar=["سعر","هترتفع","هتنزل","شراء","بيع","سولانا","بيتكوين","إيث","كريبتو"],
        keywords_en=["price","up","down","buy","sell","solana","bitcoin","eth","crypto","moon"],
        context_signals=["binance","coingecko","tradingview","chart","crypto","solana","btc"],
        weight=1.0,
    ),
    IntentTemplate(
        action="github_search",
        service="github",
        keywords_ar=["كود","ريبو","مشروع","مطور","نجوم","github"],
        keywords_en=["repo","code","project","stars","fork","github","developer","library"],
        context_signals=["github","repository","pull request","commit","branch"],
        weight=1.0,
    ),
    IntentTemplate(
        action="weather_check",
        service="weather", # Unified naming
        keywords_ar=["طقس","حرارة","مطر","جو","درجة"],
        keywords_en=["weather","temperature","rain","hot","cold","forecast","wind"],
        context_signals=["weather","map","forecast","temperature","cairo","london"],
        weight=1.0,
    ),
]


# ─────────────────────────────────────────────
# Asset Extractor
# ─────────────────────────────────────────────

ASSET_PATTERNS = {
    "bitcoin": ["bitcoin", "btc", "بيتكوين"],
    "solana":  ["solana", "sol", "سولانا"],
    "ethereum":["ethereum", "eth", "إيث", "ايثيريوم"],
    "binancecoin": ["bnb", "binance coin"],
    "cairo":   ["cairo", "القاهرة"],
    "london":  ["london", "لندن"],
}

def extract_asset(
    query: str,
    screen_ctx: Optional[ScreenContext] = None,
) -> Optional[str]:
    """
    Extract target asset from query text OR screen context.
    Screen context takes priority if query is ambiguous.
    Uses word boundary matching to avoid false positives.
    """
    query_lower = query.lower()

    # First: try query text with word boundary matching
    for canonical, aliases in ASSET_PATTERNS.items():
        for alias in aliases:
            # Use word boundary matching to avoid false positives
            # e.g., "something" should not match "eth" 
            pattern = r'\b' + re.escape(alias) + r'\b'
            if re.search(pattern, query_lower):
                return canonical

    # Second: screen context (this is the Fold-inspired magic)
    if screen_ctx:
        for asset in screen_ctx.detected_assets:
            asset_l = asset.lower()
            for canonical, aliases in ASSET_PATTERNS.items():
                if asset_l in aliases or asset_l == canonical:
                    return canonical
        # App-level hints
        app_lower = screen_ctx.detected_app.lower()
        if "solana" in app_lower: return "solana"
        if "bitcoin" in app_lower or "btc" in app_lower: return "bitcoin"

    return None


# ─────────────────────────────────────────────
# Memory Context (simplified signal)
# ─────────────────────────────────────────────

@dataclass
class MemorySignal:
    """Recent conversation history signals."""
    recent_services: List[str] = field(default_factory=list)
    recent_assets:   List[str] = field(default_factory=list)
    last_action:     Optional[str] = None
    query_count_1h:  int = 0


# ─────────────────────────────────────────────
# The Constraint Solver
# ─────────────────────────────────────────────

class AetherConstraintSolver:
    """
    Wave Function Collapse for user intent.
    Calibrated by Bayesian Feedback.
    """

    CONFIDENCE_THRESHOLD = 0.35 

    def __init__(self):
        self.feedback = AetherFeedbackLoop()

    def resolve(
        self,
        query: str,
        voice: Optional[VoiceFeatures] = None,
        screen: Optional[ScreenContext] = None,
        time_ctx: Optional[TimeContext] = None,
        memory: Optional[MemorySignal] = None,
    ) -> ResolvedIntent:
        """
        Main entry point.
        """
        logger.info(f"Resolving intent for: '{query}'")

        # Step 1: Compute urgency & tau from voice
        urgency_score = voice.urgency_score if voice else 0.3
        tau, cognitive_system = compute_tau(urgency_score)
        urgency_level = classify_urgency(urgency_score)

        # Step 2: Score all intent templates
        scores: List[Tuple[float, IntentTemplate]] = []
        
        # Load adaptive weights (Sync wait for file-based weights)
        weights = {}
        try:
            with open("agent/aether_memory/CALIBRATION.json") as f:
                raw = json.load(f)
                weights = {k: v["weight"] for k, v in raw.items()}
        except: pass

        for template in INTENT_CATALOG:
            # Apply Bayesian weight bias
            template.weight = weights.get(template.action, 1.0)
            
            score = self._score_template(
                template, query, voice, screen, time_ctx, memory
            )
            scores.append((score, template))

        # Step 3: Pick winner
        scores.sort(key=lambda x: x[0], reverse=True)
        best_score, best_template = scores[0]

        # Step 4: Extract target asset/entity
        asset = extract_asset(query, screen)
        if asset is None and memory:
            asset = (memory.recent_assets[-1]
                     if memory.recent_assets else "bitcoin")

        # Step 5: Build reasoning explanation
        reasoning = self._build_reasoning(
            best_template, best_score, voice, screen, memory
        )

        intent = ResolvedIntent(
            raw_query=query,
            action=best_template.action,
            target=asset or "unknown",
            urgency=urgency_level,
            cognitive_system=cognitive_system,
            tau=tau,
            confidence=min(best_score, 1.0),
            reasoning=reasoning,
        )

        logger.info(
            f"✅ Intent resolved: {intent.action}({intent.target}) "
            f"| τ={tau:.2f} | sys={cognitive_system.name} "
            f"| conf={intent.confidence:.0%}"
        )
        return intent

    def _score_template(
        self,
        template: IntentTemplate,
        query: str,
        voice: Optional[VoiceFeatures],
        screen: Optional[ScreenContext],
        time_ctx: Optional[TimeContext],
        memory: Optional[MemorySignal],
    ) -> float:
        score = 0.0
        query_lower = query.lower()

        # ── Keyword matching (query text) ──────────────────── 40%
        kw_score = 0.0
        all_keywords = template.keywords_ar + template.keywords_en
        # Prevent ZeroDivisionError when all_keywords is empty
        if all_keywords:
            for kw in all_keywords:
                if kw in query_lower:
                    kw_score += 1.0 / len(all_keywords)
        score += kw_score * 0.40

        # ── Screen context matching ────────────────────────── 30%
        if screen:
            screen_text = (
                screen.raw_description.lower() + " " +
                screen.detected_app.lower() + " " +
                " ".join(a.lower() for a in screen.detected_assets)
            )
            ctx_score = 0.0
            # Prevent ZeroDivisionError when context_signals is empty
            if template.context_signals:
                for signal in template.context_signals:
                    if signal.lower() in screen_text:
                        ctx_score += 1.0 / len(template.context_signals)
            score += ctx_score * 0.30

        # ── Voice transcript bonus ─────────────────────────── 15%
        if voice and voice.transcript:
            transcript_lower = voice.transcript.lower()
            kw_hit = any(
                kw in transcript_lower
                for kw in template.keywords_ar + template.keywords_en
            )
            if kw_hit:
                score += 0.15

        # ── Memory recency bias ────────────────────────────── 10%
        if memory:
            if template.service in memory.recent_services:
                score += 0.10

        # ── Time context bonus ─────────────────────────────── 5%
        if time_ctx:
            if template.action == "price_check" and time_ctx.is_market_hours:
                score += 0.05

        return score * template.weight

    def _build_reasoning(
        self,
        template: IntentTemplate,
        score: float,
        voice: Optional[VoiceFeatures],
        screen: Optional[ScreenContext],
        memory: Optional[MemorySignal],
    ) -> str:
        reasons = []
        if score > 0.3:
            reasons.append(f"keyword match ({score:.0%} confidence)")
        if screen and screen.detected_assets:
            reasons.append(f"screen shows {', '.join(screen.detected_assets)}")
        if voice and voice.urgency_score > 0.6:
            reasons.append("stressed voice detected")
        if memory and template.service in (memory.recent_services or []):
            reasons.append("recent conversation context")
        return " | ".join(reasons) if reasons else "default inference"


def build_time_context() -> TimeContext:
    """Build current time context for constraint solving."""
    now = datetime.utcnow()
    hour = now.hour
    dow  = now.weekday()  # 0=Monday
    is_weekend = dow >= 5

    # NYSE/Crypto: crypto is always open, stocks 9:30-16:00 ET (14:30-21:00 UTC)
    is_market = 14 <= hour <= 21 and not is_weekend

    if hour < 9:
        session = "pre"
    elif hour < 21:
        session = "open"
    else:
        session = "after"

    return TimeContext(
        hour=hour,
        is_market_hours=is_market,
        day_of_week=dow,
        is_weekend=is_weekend,
        market_session=session,
    )
