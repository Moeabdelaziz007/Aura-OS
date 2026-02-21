# 🌍 WORLD.md: Generative World Simulator & State Schema

```yaml
version: 0.1.1
pillar: Prometheus (World Model)
math_model: Partially_Observable_Markov_Decision_Process (POMDP)
```

## � Generative Model Specification ($m$)

The world is modeled via the following categorical matrices (A, B, C, D):

| Matrix | Name | Functional Definition |
| :--- | :--- | :--- |
| **A** | Likelihood | $P(o_t \| s_t)$: Observation probability given state. |
| **B** | Transition | $P(s_{t+1} \| s_t, a_t)$: State change given action. |
| **C** | Preferences | $P(o)$: Prior preferences over outcomes. |
| **D** | Initial Prior | $P(s_1)$: Initial belief about the UI state. |

## 🛰️ UI State Representation (Contract)

The Edge Client streams state $o_t$. WORLD.md computes the hidden state $s_t$:

```yaml
state_contract:
  perception_id: UUID
  modality: [VISUAL, DOM, AUDIO]
  content:
    visual_hash: SHA-256
    dom_entropy: float (Complexity score)
    active_node: string (XPath/ID)
```

## 🛠️ Belief Update Protocol

1. **Receive:** Capture observation $o_t$ from Edge.
2. **Infer:** Update hidden state $q(s_t)$ by minimizing VFE (see INFERENCE.md).
3. **Predict:** Use Matrix B to project $s_{t+1}$ based on proposed policy $\pi$.
4. **Evaluate:** Calculate expected surprise in $s_{t+1}$.

---
*WORLD.md is the probabilistic arena where AlphaMind plays its games.*

## 🌳 Action Space Mapping

* **Navigation:** [SCROLL, CLICK, HOVER, INPUT]
* **Reasoning:** [ALPHA_MCTS_SEARCH, CAUSAL_CHECK, SWARM_SIM]

---
*WORLD.md allows the agent to "dream" of the UI state before the Edge Client even renders it.*
