import math
import asyncio
from typing import Any, Dict, List
from .memory_parser import AuraNavigator

class HyperMindRouter:
    """
    Priority 1 Refactor: Active Inference Cognitive Gating.
    Implements VFE and EFE (G) logic (Prometheus Pillar).
    """
    def __init__(self, bridge: AuraNavigator):
        self.bridge = bridge

    async def calculate_vfe(self, context: Dict[str, Any]) -> float:
        """
        Variational Free Energy (F) = Complexity - Accuracy.
        Determines System 1 vs System 2 gating.
        """
        dna = await self.bridge.load_dna_async()
        
        # Accuracy: How well our internal WORLD.md predicts current sensory anomaly
        # In this scale, higher anomaly = lower accuracy = higher surprise
        surprise_signal = float(context.get("anomaly", 0.0))
        
        # Complexity: The cost of updating beliefs (entropy bias) pulled from DNA
        dna = await self.bridge.load_dna_async()
        complexity_bias = dna.inference.get("complexity_bias", 0.05)
        
        vfe = complexity_bias + surprise_signal
        return vfe

    async def calculate_efe(self, context: Dict[str, Any]) -> float:
        """
        Expected Free Energy (G) = Epistemic Value + Pragmatic Value.
        Determines the 'Curiosity' vs 'Compliance' of the response.
        """
        dna = await self.bridge.load_dna_async()
        weights = dna.inference.get("cognitive_weights", {})
        
        # 1. Epistemic Value (Discovery): Driven by curiosity weights
        epistemic = weights.get("epistemic_curiosity (info)", 0.5) * context.get("novelty", 0.1)
        
        # 2. Pragmatic Value (Utility): Driven by pragmatic utility weights
        pragmatic = weights.get("pragmatic_utility (pref)", 0.5) * context.get("goal_alignment", 1.0)
        
        # G (EFE) = Complexity (Fixed) - Epistemic - Pragmatic
        # We minimize G to select the optimal policy
        g_score = 1.0 - (epistemic + pragmatic)
        return g_score
    
    async def update_cognitive_weights(self, feedback: float, lr: float = 0.01):
        """Adjusts the cognitive weights by a bounded gradient step based on feedback.

        `feedback` is a reward signal (positive for good policies, negative for bad).
        Updates are clamped to a maximum percentage change relative to the
        original baseline stored in SOUL.md to avoid catastrophic identity drift.
        A cooldown period (default 60s) prevents continuous violent updates.
        """
        dna = await self.bridge.load_dna_async(force=False)
        weights = dna.inference.setdefault("cognitive_weights", {})
        # baselines are stored separately to compute percentage change
        baselines = dna.inference.setdefault("cognitive_baselines", {})
        timestamp = dna.inference.setdefault("cognitive_last_update", 0)
        now = asyncio.get_event_loop().time()

        # cooldown: at least 60 seconds between updates ("Cognitive Sleep")
        if now - timestamp < 60:
            return

        # initialize if missing; baseline read from SOUL.md if available
        soul = dna.soul
        for key, init in [("epistemic_curiosity (info)", 0.5),
                          ("pragmatic_utility (pref)", 0.5),
                          ("surprise_threshold (tau)", 0.15)]:
            weights.setdefault(key, init)
            # baseline either already stored or taken from SOUL defaults
            if key not in baselines:
                baselines[key] = soul.get("defaults", {}).get(key, weights[key])

        # compute proposed new values
        for key in ["epistemic_curiosity (info)", "pragmatic_utility (pref)"]:
            current = weights[key]
            updated = current + lr * feedback
            # clamp deviation to ±10% of baseline value (SOUL-derived)
            base = baselines[key]
            max_delta = 0.1 * base
            delta = updated - current
            if delta > max_delta:
                updated = current + max_delta
            elif delta < -max_delta:
                updated = current - max_delta
            # keep in [0,1]
            weights[key] = min(max(updated, 0), 1)
        # complexity bias remains bounded but not tied to baseline
        bias = dna.inference.get("complexity_bias", 0.05)
        bias += lr * (-feedback)
        dna.inference["complexity_bias"] = min(max(bias, 0.0), 1.0)

        # record timestamp; note: do NOT write to disk until AuraEvolve batch run
        dna.inference["cognitive_last_update"] = now
        self.bridge.dna_cache = dna

        # NOTE: actual file persistence should be handled offline by AuraEvolve
        # during idle periods (`Cognitive Sleep`).

    async def route_action(self, context: Dict[str, Any]) -> str:
        """
        The Gating Logic Ceremony:
        1. Calculate F (VFE).
        2. If F > Tau: Engage System 2 (Reflective Search).
        3. Else: Engage System 1 (Direct Reflex).
        """
        dna = await self.bridge.load_dna_async()
        tau = dna.inference.get("cognitive_weights", {}).get("surprise_threshold (tau)", 0.15)
        
        # pre-route enrichment: consult Aura-Nexus for similar memories
        try:
            hits = await self.bridge.search_nexus(context)
            context["nexus_hits"] = hits
            if hits:
                print(f"🔗 Nexus context: {len(hits)} nodes retrieved")
        except Exception:
            pass

        f_score = await self.calculate_vfe(context)
        
        print(f"🧠 AetherCore Inference: F={f_score:.4f}, Tau={tau}")

        if f_score >= tau:
            print("🧘 VFE Breached! Engaging System 2 (Neural Swarm)...")
            return "SYSTEM_2_SWARM"
        
        return "SYSTEM_1_REFLEX"
