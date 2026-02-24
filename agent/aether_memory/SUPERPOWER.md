# ⚡ SUPERPOWER.md: Swarm Orchestration & Adaptive Pruning

```yaml
version: 1.0.0
pillar: QuantumWeaver (Execution Efficiency)
logic: Entropy-to-Swarm Mapping (Adaptive Scaling)
```

## 📐 Adaptive Swarm Pruning

The number of parallel execution nodes ($N_{swarm}$) is a function of the **State Entropy** $H(X)$:

$$N_{swarm} = \min(N_{max}, \lceil \alpha \cdot H(X) + \beta \rceil)$$

### 📊 Entropy Mapping Matrix

| Entropy $H(X)$ | Scenario | Node Count ($N$) | Pruning Strategy |
| :--- | :--- | :--- | :--- |
| **LOW** (< 0.2) | Standard Login / Known UI | 1-2 | Direct Reflex Path |
| **MEDIUM** (0.2 - 0.6) | New Page / Multi-Step Form | 3-5 | BFS Search |
| **HIGH** (> 0.6) | Chaotic UI / Dynamic Content | 8-10 (Max) | Alpha-Beta Pruning |

## ✂️ Alpha-Beta Early Termination (The Veto)

To prevent "Swarm Bankruptcy", any node that deviates from the **Causal Path** (`CAUSAL.md`) is terminated within 50ms:

1. **Path Cost Estimation:** Each node reports a projected VFE ($F$) after the first 2 actions.
2. **Dynamic Pruning:** If $F_{node} > R_{threshold}$ (where $R$ is the baseline of the best performing node), the node is signal-killed.

---
*SUPERPOWER.md: Intelligence is not just doing; it is knowing what NOT to do.*
