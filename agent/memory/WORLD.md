# 🌍 WORLD.md: Generative World Simulator (Latent POMDP)

```yaml
version: 0.2.0
pillar: Prometheus (World Model)
math_model: Latent_POMDP
compression: Variational_Autoencoder_Style
```

## 💎 Latent Space Compression ($z$)

To prevent **State Space Explosion**, mathematical inference does not operate on raw DOM/Pixels. It operates on a compressed latent vector $z_t \in \mathbb{R}^n$ where $n \ll \text{dim}(o_t)$.

* **Encoder ($E_\phi$):** $z_t \approx q_\phi(z_t | o_t)$. Maps raw UI observations (pixels/text) to a deterministic low-dimensional manifold.
* **Decoder ($D_\theta$):** $\hat{o}_t \approx p_\theta(o_t | z_t)$. Used by System 2 to "imagine" and visualize predicted outcomes.

## 📐 Latent-space Categorical Matrices

Matrices now map transitions and likelihoods within the compressed space:

| Matrix | Mapping | functional_definition |
| :--- | :--- | :--- |
| **A** | $P(z_t \| s_t)$ | Likelihood: Maps hidden beliefs to latent coordinates. |
| **B** | $P(s_{t+1} \| s_t, a_t)$ | Transition: The "Physics" of the UI in latent space. |
| **C** | $P(z^*)$ | Preference: Target "Reward" coordinates in latent space. |
| **D** | $P(s_1)$ | Initial Prior: Starting belief on cold boot. |

## 🛰️ UI State Representation (Contract)

The Edge Client streams $o_t$. The Internal Encoder consumes it:

```yaml
latent_contract:
  perception_id: UUID
  raw_dim: [width, height, dom_nodes]
  latent_vector_z: [float1, float2, ... floatN] # Size N=128
  compression_fidelity: float [0, 1]
  anomaly_signal: float # Residual error (o - Decoder(z))
```

---
*WORLD.md: The world is too big to remember; we only remember its essence (z).*

## 🛠️ Belief Update Protocol

1. **Receive:** Capture observation $o_t$ from Edge.
2. **Infer:** Update hidden state $q(s_t)$ by minimizing VFE (see INFERENCE.md).
3. **Predict:** Use Matrix B to project $s_{t+1}$ based on proposed policy $\pi$.
4. **Evaluate:** Calculate expected surprise in $s_{t+1}$.

---
*WORLD.md is the probabilistic arena where AlphaMind plays its games.*

## 🌳 Action Space Mapping

The Action Space $\mathcal{A}$ is quantized by the DNA toolset:

```yaml
action_quantization:
  - id: A_REFLEX
    tool: execute_ui_action
    latency_target: <150ms
    vfe_cost: low
  - id: A_SWARM
    tool: trigger_quantum_swarm
    latency_target: <5000ms
    vfe_cost: high (Precision-driven)
```

---
*WORLD.md allows the agent to "dream" of the UI state before the Edge Client even renders it.*
