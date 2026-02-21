# 🧠 INFERENCE.md: Active Inference & Gating Logic

```yaml
version: 0.1.1
pillar: Prometheus (Cognitive Engine)
math_model: Variational_Free_Energy (VFE) + Expected_Free_Energy (EFE)
```

## 📐 The Objective Function

AuraOS minimizes total Free Energy $F$.

### 1. Variational Free Energy (Perception)

$F \approx \underbrace{D_{KL}[q(s) \| p(s | o)]}_{\text{Inaccuracy}} + \underbrace{D_{KL}[q(s) \| p(s)]}_{\text{Complexity}}$
*Goal: Update internal beliefs to match observations.*

### 2. Expected Free Energy (Planning)

For a policy $\pi$, we compute $G(\pi)$:
$G(\pi) \approx \underbrace{E_{q(o, s | \pi)} [\ln q(s | \pi) - \ln p(o, s | \pi)]}_{\text{Epistemic + Pragmatic Value}}$

* **Epistemic Value:** Information gain (reducing uncertainty in WORLD.md).
* **Pragmatic Value:** Preference satisfaction (achieving goals in SOUL.md).

## 📏 Parameters

| Parameter | Symbol | Value | Description |
| :--- | :--- | :--- | :--- |
| **Surprise Threshold** | $\tau$ | 0.15 | Trigger System 2 if Prediction Error > $\tau$ |
| **Target Energy** | $F_{target}$ | < 0.05 | Desired state equilibrium |
| **Precision (γ)** | $\gamma$ | 1.0 | Belief confidence weighting |
| **Search Depth** | $d$ | 5 | AlphaMind MCTS steps |

## 🕹️ System 1/2 Gating Protocol (The Switch)

### 🏎️ System 1 (Reflexive Mode)

* **Trigger:** Confidence > 0.85 AND $\Delta F < \tau$.
* **Action:** Direct LLM Inference. Exploits high-probability heuristics.
* **Latency Goal:** < 200ms.

### 🧘 System 2 (Reflective Mode)

* **Trigger:** $\Delta F > \tau$ (High Surprise / Novelty).
* **Action:**
    1. **Epistemic Search:** Trigger AlphaMind MCTS to minimize $G(\pi)$.
    2. **Swarm Simulation:** QuantumWeaver tests parallel hypotheses.
    3. **Wavefront Collapse:** Converge on policy $\pi^*$ with lowest $G$.
* **Latency Goal:** Accuracy-first (Strategic).

---
> "The agent exists to minimize surprise and maximize preference."
