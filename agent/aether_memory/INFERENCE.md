# 🧠 INFERENCE.md: Active Inference & Gating Logic

```yaml
version: 0.3.0
pillar: Prometheus (Cognitive Engine)
math_model: VFE + EFE (Active Inference)
```

## 📊 Adaptive Learning Configuration

Cognitive weights adapt dynamically based on feedback signals:

| Parameter | Type | Default | Range | Purpose |
|:---|:---|:---|:---|:---|
| `learning_rate` | float | 0.01 | [0.001, 0.1] Rate of weight adjustment |
| `update_frequency` | integer | 100 | Decisions between weight updates |
| `exploration_rate` | float | 0.1 | [0, 0.3] Probability of random exploration |
| `history_size` | integer | 1000 | Decisions to store for analysis |

## 📐 Expected Free Energy ($G$)

Planning in AetherOS is the selection of a policy $\pi$ that minimizes the *Expected* Free Energy $G(\pi)$:

$$G(\pi, \tau) = \underbrace{E_{q(o, s | \pi)} [ \ln q(s | \pi) - \ln p(o, s | \pi) ]}_{\text{Total Loss}}$$

Calculated by the Orchestrator as:
$G \approx \text{Complexity} - \underbrace{\text{Epistemic Value}}_{\text{Discovery}} - \underbrace{\text{Pragmatic Value}}_{\text{Utility}}$

## ⚙️ Orchestrator Cognitive Weights

These weights determine the "curiosity" vs "compliance" of the agent:

```yaml
cognitive_weights:
  pragmatic_utility (pref): 0.85 # Drive to reach SOUL goals
  epistemic_curiosity (info): 0.65 # Drive to explore unknown UI elements
  novelty_bias: 0.25 # Preference for new states
  surprise_threshold (tau): 0.15 # System 1 -> 2 Switch
  policy_selection:
    algorithm: Dirichlet_Sampling
    temperature: 0.05 # Low temperature = Deterministic
adaptive_learning:
  enabled: true
  cooldown_period: 60s # Minimum time between updates
  max_deviation: 0.1 # Maximum ±10% change from baseline
```

### 🔄 Dynamic Tau Adjustment

The surprise threshold $\tau$ adapts based on context:

$$\tau_{dynamic} = \tau_{base} \cdot (1 + \alpha \cdot \text{urgency} - \beta \cdot \text{frustration})$$

Where:
- $\tau_{base} = 0.15$ (default threshold)
- $\alpha = 0.5$ (urgency scaling factor)
- $\beta = 0.3$ (frustration reduction factor)

High urgency reduces $\tau$ (forcing System 1), while high frustration increases $\tau$ (forcing System 2 for explanation).

### 📈 Performance Metrics

Decision quality is tracked continuously:

```yaml
performance_metrics:
  accuracy: 0.92 # Percentage of correct predictions
  avg_latency_ms: 145 # Average decision time
  system1_ratio: 0.78 # Percentage of System 1 decisions
  system2_ratio: 0.22 # Percentage of System 2 decisions
  last_update: 1707234567890 # Timestamp of last weight update
```

## 📏 System 1/2 Gating Protocol

### 🏎️ System 1 (Reflexive)

* **Trigger:** Prediction Error $\Delta F < \tau$.
* **Inference:** $q(s) \to a_{direct}$.
* **Latency:** < 150ms.

### 🧘 System 2 (Reflective)

* **Trigger:** $\Delta F \ge \tau$ OR Explicit User Query.
* **Search:** AetherMind MCTS search on latent manifold $z$.
* **Loop:** GIF-MCTS (Identify -> Fix -> Verify).

### 🎲 Exploration vs Exploitation

The agent balances exploration and exploitation using epsilon-greedy strategy:

$$P(explore) = \epsilon \cdot (1 - \text{confidence})$$

Where:
- $\epsilon = 0.1$ (base exploration rate)
- $\text{confidence}$ is the prediction confidence from WORLD.md

High confidence favors exploitation (known actions), while low confidence favors exploration (new actions).

### 📝 Decision History

Recent decisions are stored for learning:

```yaml
decision_history:
  - context:
      anomaly: 0.05
      novelty: 0.1
      goal_alignment: 1.0
    decision: SYSTEM_1_REFLEX
    vfe_score: 0.08
    outcome: SUCCESS
    timestamp: 1707234567890
  # ... more decisions ...
```

This history enables:
- Pattern recognition in decision-making
- Identification of systematic biases
- Continuous improvement of cognitive weights

---
*Inference is a battle between what the agent knows and what it needs to find out.*
