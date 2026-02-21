# 🧠 INFERENCE.md: Active Inference & Gating Logic

```yaml
version: 0.1.0
pillar: Prometheus (Cognitive Engine)
math_model: Variational_Free_Energy (VFE)
```

## 📐 Mathematical Targets

Minimize Free Energy $F$:
$$F = \text{Complexity} - \text{Accuracy}$$

| Parameter | Symbol | Value | Description |
| :--- | :--- | :--- | :--- |
| **Surprise Threshold** | $\tau$ | 0.15 | Trigger System 2 if Prediction Error > $\tau$ |
| **Target Energy** | $F_{target}$ | < 0.05 | Desired state equilibrium |
| **Learning Rate** | $\eta$ | 0.001 | Rate of WORLD.md model updates |
| **Search Depth** | $d$ | 5 | AlphaMind MCTS steps |

## 🕹️ System 1/2 Gating Protocol (The Switch)

### 🏎️ System 1 (Reflexive Mode)

* **Trigger:** Confidence > 0.85 AND $\Delta F < \tau$.
* **Action:** Direct LLM Inference. No MCTS. No Swarm.
* **Latency Goal:** < 200ms.

### 🧘 System 2 (Reflective Mode)

* **Trigger:** Unexpected UI state OR $\Delta F > \tau$.
* **Action:**
    1. Pause Perception Stream.
    2. Spawn QuantumWeaver Swarm (Cloud Run).
    3. Engage AlphaMind MCTS search on Shadow DOM.
    4. Collapse winning strategy.
* **Latency Goal:** Optimized for Accuracy, not Speed.

---
> "Act reflexively on the known; reflect deeply on the unknown."
