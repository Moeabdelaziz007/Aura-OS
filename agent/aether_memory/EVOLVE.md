# 🧬 EVOLVE.md: Recursive Self-Healing & Mutation Rules

```yaml
version: 0.3.0
pillar: AetherEvolve (Evolution Engine)
strategy: VerMCTS (Verified MCTS) + GIF-MCTS
```

## 📊 Evolution Configuration

The self-healing circuit operates with the following parameters:

| Parameter | Type | Default | Range | Purpose |
|:---|:---|:---|:---|:---|
| `mutation_budget` | integer | 10 | [1, 50] Maximum mutations per day |
| `rollback_enabled` | boolean | true | - Ability to revert failed mutations |
| `ab_testing` | boolean | true | - Enable A/B testing for mutations |
| `sample_size` | integer | 100 | [10, 1000] Sample size for A/B tests |
| `history_size` | integer | 1000 | [100, 10000] Evolution history to keep |

## 📐 Reward Function ($R$)

The system evolves to optimize:
$R = \alpha \cdot P_{success} - \beta \cdot T_{exec} - \gamma \cdot C_{code}$

Where:
- $\alpha = 1.0$ (Success weight)
- $\beta = 0.001$ (Latency penalty per ms)
- $\gamma = 0.01$ (Code complexity penalty per line)

## 🧪 Mutation Protocols (GIF-MCTS Loop)

When a "Pain Signal" (Error/Anomaly) triggers the circuit:

1. **Generate:** NeuroSage identifies the root cause via Counterfactual Trace (see CAUSAL.md).
2. **Improve:** AetherMind spawns a **VerMCTS** tree. Unlike standard MCTS, every leaf node must be verified by the NeuroSage symbolic guard.
3. **Fix (GIF Strategy):**
    * **Rethink Stage:** If a mutation fails execution, the error log is fed back into the search as a negative prior.
    * **Swarm Backtest:** Mutations are tested in parallel on the Cloud Run Shadow DOM.

## 📈 Skill Promotion Criteria

A skill is automatically promoted from **System 2** to **System 1** (Native-Aether-Skill) when:

```yaml
promotion_criteria:
  success_threshold: 0.90    # Minimum success rate
  usage_threshold: 50          # Minimum usage count
  latency_threshold: 150          # Maximum average latency (ms)
  stability_period: 1000         # Minimum decisions in stable state
```

Promoted skills are moved to the high-priority section of [`SKILLS.md`](agent/memory/SKILLS.md) for reflexive execution.

## 🔄 Rollback Mechanism

When a mutation fails or degrades performance:

1. **Detection:** Performance drop > 20% from baseline
2. **Trigger:** Automatic rollback to previous stable state
3. **Logging:** Failed mutation is logged with reason
4. **Blacklisting:** Failed mutation pattern is temporarily blacklisted

```yaml
rollback_config:
  performance_drop_threshold: 0.20  # 20% drop triggers rollback
  max_rollback_attempts: 3
  blacklist_duration: 3600s  # 1 hour blacklist
```

## 🧪 A/B Testing

Mutations are tested before full deployment:

```yaml
ab_testing:
  enabled: true
  sample_size: 100
  min_confidence: 0.95
  statistical_significance: 0.05
```

A mutation is only deployed if:
- Success rate > baseline + 5%
- Statistical significance (p < 0.05)
- No increase in latency > 10%

## 🧬 Skill Consolidation

* **Aether-Discovery:** Successfully verified mutations are not just patched; they are distilled into a "Skill Template" and appended to [`SKILLS.md`](agent/memory/SKILLS.md).
* **Weight Decay:** Old, unused skills lose proficiency over time to prevent "DNA Bloat".

### Aether-Consolidation

Ephemeral working memories that originate during a task are candidates for permanent
synaptic links in [`NEXUS.md`](agent/memory/NEXUS.md) only after passing the **NeuroSage Causal Validation**.
Each candidate trace is replayed against the SCM; if a counterfactual alternative
yields a higher reward $R$, the trace is tagged `permanent` and merged into the
Aether-Nexus graph with an initial `strength` value derived from success probability.

*Skills used frequently during reflexive or swarm routines automatically undergo
promotion.*  When a `skill` appears in the top 5 actions for more than 50 tasks,
AetherEvolve renames it from a `Swarm-Simulation` entry to a `Native-Aether-Skill`
and moves it into the high‑priority section of [`SKILLS.md`](agent/memory/SKILLS.md). This reduces planning
latency by enabling System 1 execution.

## 📜 Evolution History

All evolutionary changes are logged for analysis:

```yaml
evolution_history:
  - mutation_id: "ev_001"
    timestamp: 1707234567890
    type: "skill_promotion"
    target: "execute_ui_action"
    before:
      proficiency_score: 0.85
      usage_count: 45
    after:
      proficiency_score: 0.92
      usage_count: 50
    outcome: SUCCESS
    reward_delta: 0.07
  # ... more history ...
```

This history enables:
- Tracking of system improvement over time
- Identification of successful mutation patterns
- Reverting to previous stable states if needed

---
*AetherOS: The first agent designed to survive its own mistakes.*
---
*AetherOS is a living algorithm. It never makes the same mistake twice.*
---
*Evolution is not just repair; it is the art of crystallizing what works.*
