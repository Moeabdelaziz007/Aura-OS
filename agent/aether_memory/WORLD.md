# 🌍 WORLD.md: Generative World Simulator (Latent POMDP)

```yaml
version: 0.3.0
pillar: Prometheus (World Model)
math_model: Latent_POMDP
compression: Variational_Autoencoder_Style
```

## ⚙️ Adaptive Latent Configuration

The latent space dimensions and parameters adapt dynamically based on UI complexity:

| Parameter | Type | Default | Range | Purpose |
|:---|:---|:---|:---|:---|
| `latent_dim` | adaptive | 64-256 | Dynamic dimension of latent vector $z_t$ based on complexity |
| `confidence_threshold` | float | 0.75 | [0, 1] Minimum confidence for prediction acceptance |
| `anomaly_threshold` | float | 2.5 | Standard deviations for anomaly detection |
| `temporal_window` | integer | 30 | Frames to track for temporal patterns |
| `transition_history_size` | integer | 1000 | Number of successful transitions to store |

## 💎 Latent Space Compression ($z$)

To prevent **State Space Explosion**, mathematical inference does not operate on raw DOM/Pixels. It operates on a compressed latent vector $z_t \in \mathbb{R}^n$ where $n \ll \text{dim}(o_t)$.

* **Encoder ($E_\phi$):** $z_t \approx q_\phi(z_t | o_t)$. Maps raw UI observations (pixels/text) to a deterministic low-dimensional manifold.
* **Decoder ($D_\theta$):** $\hat{o}_{t:t+k} \approx p_\theta(o_{t:t+k} | z_t)$. Used by System 2 to "imagine" and visualize predicted **multi-frame video trajectories** (Spatio-Temporal Futures).

### 🎯 Dynamic Dimension Adjustment

The latent dimension $n$ adapts based on UI complexity:

$$n = \min(256, \max(64, \lceil \alpha \cdot H(X) + \beta \rceil))$$

Where:
- $H(X)$ is the entropy of the current UI state
- $\alpha = 100$ (entropy scaling factor)
- $\beta = 64$ (minimum dimension baseline)

This ensures efficient memory usage while preserving sufficient representational capacity.

### 🔍 Anomaly Detection

Anomalies are detected using Mahalanobis distance in latent space:

$$D_M(z_t) = \sqrt{(z_t - \mu)^T \Sigma^{-1} (z_t - \mu)}$$

If $D_M(z_t) > \text{anomaly\_threshold} \cdot \sigma$, the state is flagged as novel and triggers System 2 exploration.

## 📐 Latent-space Categorical Matrices

Matrices now map transitions and likelihoods within the compressed spatio-temporal space:

| Matrix | Mapping | functional_definition |
| :--- | :--- | :--- |
| **A** | $P(z_t \| s_t)$ | Likelihood: Maps hidden beliefs to latent coordinates. |
| **B** | $P(z_{t+k} \| z_t, a_t)$ | Transition: Predictive video simulation (The "Physics" of the UI). |
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
5. **Store:** If prediction confidence > threshold, store transition in history.

### 📊 Transition History

Successful transitions are stored for learning:

```yaml
transition_history:
  - source_z: [0.12, 0.03, ...]
    action: CLICK
    target_z: [0.15, 0.04, ...]
    confidence: 0.92
    timestamp: 1707234567890
  # ... more transitions ...
```

This history is used to:
- Reinforce successful action patterns
- Identify common UI transitions
- Accelerate System 1 reflexive responses

---
*WORLD.md is the probabilistic arena where AetherMind plays its games.*

## 🌳 Action Space Mapping

The Action Space $\mathcal{A}$ is quantized by the DNA toolset:

```yaml
action_quantization:
  - id: A_REFLEX
    tool: execute_ui_action
    latency_target: <150ms
    vfe_cost: low
  - id: A_SHELL
    tool: shell_execute
    latency_target: <300ms
    vfe_cost: medium
  - id: A_FILE
    tool: filesystem_manage
    latency_target: <100ms
    vfe_cost: low
  - id: A_SEARCH
    tool: knowledge_search
    latency_target: <2000ms
    vfe_cost: low
```

---
*WORLD.md allows the agent to "dream" of the UI state before the Edge Client even renders it.*
