# 🧬 EVOLVE.md: Recursive Self-Healing & Mutation Rules

```yaml
version: 0.2.0
pillar: AuraEvolve (Evolution Engine)
strategy: VerMCTS (Verified MCTS) + GIF-MCTS
```

## 📐 Reward Function ($R$)

The system evolves to optimize:
$R = \alpha \cdot P_{success} - \beta \cdot T_{exec} - \gamma \cdot C_{code}$

## 🧪 Mutation Protocols (GIF-MCTS Loop)

When a "Pain Signal" (Error/Anomaly) triggers the circuit:

1. **Generate:** NeuroSage identifies the root cause via Counterfactual Trace (see CAUSAL.md).
2. **Improve:** AlphaMind spawns a **VerMCTS** tree. Unlike standard MCTS, every leaf node must be verified by the NeuroSage symbolic guard.
3. **Fix (GIF Strategy):**
    * **Rethink Stage:** If a mutation fails execution, the error log is fed back into the search as a negative prior.
    * **Swarm Backtest:** Mutations are tested in parallel on the Cloud Run Shadow DOM.

## 🧬 Skill Consolidation

* **Aura-Discovery:** Successfully verified mutations are not just patched; they are distilled into a "Skill Template" and appended to `SKILLS.md`.
* **Weight Decay:** Old, unused skills lose proficiency over time to prevent "DNA Bloat".

---
*AuraOS: The first agent designed to survive its own mistakes.*

---
*AuraOS is a living algorithm. It never makes the same mistake twice.*

## 🔷 Aura-Consolidation (New)

Ephemeral working memories that originate during a task are candidates for permanent
synaptic links in `NEXUS.md` only after passing the **NeuroSage Causal Validation**.
Each candidate trace is replayed against the SCM; if a counterfactual alternative
yields a higher reward $R$, the trace is tagged `permanent` and merged into the
Aura-Nexus graph with an initial `strength` value derived from success probability.

*Skills used frequently during reflexive or swarm routines automatically undergo
promotion.*  When a `skill` appears in the top 5 actions for more than 50 tasks,
AuraEvolve renames it from a `Swarm-Simulation` entry to a `Native-Aura-Skill`
and moves it into the high‑priority section of `SKILLS.md`. This reduces planning
latency by enabling System 1 execution.

---
*Evolution is not just repair; it is the art of crystallizing what works.*
