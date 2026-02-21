# ⚖️ CAUSAL.md: Neuro-Symbolic Causal Graphs

```yaml
version: 0.1.1
pillar: NeuroSage (Logic Guard)
model: Structural_Causal_Model (SCM)
```

## 📐 The Causal Graph (DAG)

AuraOS reasons over a Structural Causal Model $M = \langle S, U, F \rangle$:

* $S$: Set of UI state variables (e.g., `is_authenticated`, `button_clickable`).
* $U$: Unobserved background variables.
* $F$: Functional relationships (e.g., $f_{transaction} = \text{Balance} > \text{Cost}$).

## 🛡️ Structural Guardians (Interventions)

NeuroSage uses the **do-calculus** operator $P(y | do(x))$ to simulate deterministic interventions:

```yaml
causal_interventions:
  EXECUTE_UI_ACTION:
    nodes: [s_focus, s_reflex, s_trust]
    logic: |
      P(s_reflex | do(execute_ui_action))
      Condition: VFE < tau AND trust_verified(SOUL.md)
  TRIGGER_QUANTUM_SWARM:
    nodes: [s_complexity, s_reflection, s_discovery]
    logic: |
      P(s_discovery | do(trigger_quantum_swarm))
      Condition: VFE >= tau OR explicit_query == TRUE
```

## 🔍 Counterfactual Reasoning

If an action fails, NeuroSage asks: *"What would have happened if I had clicked $Y$ instead of $X$?"*

* **Trace:** Rollback WORLD.md belief state.
* **Mutate:** Apply $do(a')$ to the DAG.
* **Evaluate:** If $R_{a'} > R_{a}$, log as a Mutation Signal for EVOLVE.md.

---
*NeuroSage: Moving AI from correlation to causation.*
