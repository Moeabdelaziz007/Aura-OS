# 🌍 WORLD.md: Generative World Simulator & State Schema

```yaml
version: 0.1.0
pillar: Prometheus (World Model)
schema_type: Hierarchical_V-DOM
```

## 🛰️ UI State Representation (Contract)

The Edge Client MUST stream state using the following JSON/YAML format. WORLD.md translates this into a "Generative Belief State" $s_t$:

```yaml
state_contract:
  perception_id: UUID
  timestamp: ISO-8601
  modality: [VISUAL, DOM, AUDIO]
  content:
    visual_hash: SHA-256
    dom_tree_summary: 
      depth: integer
      interactive_elements_count: integer
      active_node_xpath: string
    audio_sentiment: float [-1.0, 1.0]
  spatial_mapping:
    resolution: [width, height]
    focus_point: [x, y]
```

## 🕯️ Generative Simulation Parameters

* **Temporal Horizon:** 5 actions ahead.
* **Confidence Threshold (P):** 0.85 (Actionable)
* **Drift Sensitivity:** High. Trigger re-scan if $s_{t+1}$ deviates > 15% from prediction.

## 🌳 Action Space Mapping

* **Navigation:** [SCROLL, CLICK, HOVER, INPUT]
* **Reasoning:** [ALPHA_MCTS_SEARCH, CAUSAL_CHECK, SWARM_SIM]
* **Evolution:** [MUTATE_LOGIC, UPDATE_SKILL]

---
*WORLD.md allows the agent to "dream" of the UI state before the Edge Client even renders it.*
