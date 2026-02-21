import math
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
        
        # Complexity: The cost of updating beliefs (simulated as entropy bias)
        complexity_bias = 0.05 
        
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
        """Adjusts the cognitive weights by a simple gradient step based on feedback.

        `feedback` is a reward signal (positive for good policies, negative for bad).
        We nudge both epistemic and pragmatic weights as well as complexity bias.
        """
        dna = await self.bridge.load_dna_async(force=False)
        weights = dna.inference.setdefault("cognitive_weights", {})
        # initialize if missing
        weights.setdefault("epistemic_curiosity (info)", 0.5)
        weights.setdefault("pragmatic_utility (pref)", 0.5)
        weights.setdefault("surprise_threshold (tau)", 0.15)
        # simple gradient update (reinforcement-like)
        weights["epistemic_curiosity (info)"] += lr * feedback
        weights["pragmatic_utility (pref)"] += lr * feedback
        # keep in [0,1]
        weights["epistemic_curiosity (info)"] = min(max(weights["epistemic_curiosity (info)"],0),1)
        weights["pragmatic_utility (pref)"] = min(max(weights["pragmatic_utility (pref)"],0),1)
        # update complexity bias separately
        dna.inference["complexity_bias"] = dna.inference.get("complexity_bias",0.05) + lr * (-feedback)
        # write back the dna cache (note: file persists via AuraNavigator later)
        self.bridge.dna_cache = dna

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
            hits = self.bridge.search_nexus(context)
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
