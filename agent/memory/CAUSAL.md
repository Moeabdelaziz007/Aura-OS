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
  CRITICAL_ACTION:
    nodes: [s_focus, s_trust, s_gate]
    logic: |
      do(ACTION) IS PERMITTED ONLY IF:
      - node(s_trust) == 1.0 (Verified via SOUL.md)
      - node(s_gate) == 1.0 (Verified via INFERENCE.md)
      - PARRENT(ACTION) contains {Verification_Node}
```

## 🔍 Counterfactual Reasoning

If an action fails, NeuroSage asks: *"What would have happened if I had clicked $Y$ instead of $X$?"*

* **Trace:** Rollback WORLD.md belief state.
* **Mutate:** Apply $do(a')$ to the DAG.
* **Evaluate:** If $R_{a'} > R_{a}$, log as a Mutation Signal for EVOLVE.md.

---
*NeuroSage: Moving AI from correlation to causation.*
