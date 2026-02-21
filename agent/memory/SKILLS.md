# 🛠️ SKILLS.md: Executable Tool Registry (Gemini Live Contract)

```yaml
version: 1.0.0
pillar: NeuroSage (Action Space)
contract_type: Google_GenAI_Function_Declaration
```

## 📐 Gating Mathematics ($F$ & $G$)

Before any tool is executed, the `HyperMindRouter` performs a **Causal Veto Check**:

1. **Variational Free Energy ($F$):**
   - $F = \text{Complexity} - \text{Accuracy}$.
   - If $F < \tau$ (Surprise Threshold), the tool is executed via System 1 (Reflex).
   - If $F \ge \tau$, the tool is diverted to System 2 (Swarm Simulation) to evaluate Expected Free Energy.

2. **Expected Free Energy ($G$):**
   - $G(\pi) = \underbrace{E_q [\ln q(s) - \ln p(o, s)]}_{\text{Risk}} + \underbrace{E_q [\ln q(s)]}_{\text{Ambiguity}}$.
   - $G \approx \text{Complexity} - \text{Epistemic} - \text{Pragmatic}$.

---

## 🧰 Executable Toolset (JSON Schema)

### 🏎️ `execute_ui_action` (System 1)

Direct reflexive interaction with the Edge Client.

```yaml
function_declaration:
  name: execute_ui_action
  description: Executes a direct UI interaction on the OS via the Synaptic Bridge.
  parameters:
    type: object
    properties:
      action_type:
        type: string
        enum: [CLICK, TYPE, SCROLL, DRAG, WAIT]
        description: The atomic action to perform.
      x:
        type: integer
        description: X-coordinate (normalized 0-1000).
      y:
        type: integer
        description: Y-coordinate (normalized 0-1000).
      value:
        type: string
        description: Text to type or duration to wait.
    required: [action_type]
```

### 🧘 `trigger_quantum_swarm` (System 2)

High-surprise, complex problem solving via parallel simulation.

```yaml
function_declaration:
  name: trigger_quantum_swarm
  description: Triggers a parallel swarm of ephemeral nodes to simulate UI trajectories.
  parameters:
    type: object
    properties:
      latent_state_z:
        type: array
        items: {type: number}
        description: The current compressed belief vector z_t (dim=128).
      objective:
        type: string
        description: The high-level target state to reach.
    required: [latent_state_z, objective]
```

---
*SKILLS.md is the executable muscle of the AetherCore.*
