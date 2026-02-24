# ⚖️ CAUSAL.md: Neuro-Symbolic Causal Graphs

```yaml
version: 0.2.0
pillar: NeuroSage (Logic Guard)
model: Structural_Causal_Model (SCM)
```

## 📐 The Causal Graph (DAG)

AetherOS reasons over a Structural Causal Model $M = \langle S, U, F \rangle$:

* $S$: Set of UI state variables (e.g., `is_authenticated`, `button_clickable`).
* $U$: Unobserved background variables.
* $F$: Functional relationships (e.g., $f_{transaction} = \text{Balance} > \text{Cost}$).

  SHELL_EXECUTE:
    nodes: [s_terminal, s_os_state, s_safety]
    logic: |
      P(s_os_state | do(shell_execute))
      Block if: command.contains(['rm -rf', 'mkfs', 'dd']) AND user_override == FALSE
  FILESYSTEM_MANAGE:
    nodes: [s_data_integrity, s_storage, s_gate]
    logic: |
      P(s_data_integrity | do(filesystem_manage))
      Condition: path.is_within_sandbox() OR s_gate == 1.0
  KNOWLEDGE_SEARCH:
    nodes: [s_epistemic, s_accuracy]
    logic: |
      P(s_accuracy | do(knowledge_search))

## 🔍 Counterfactual Reasoning

If an action fails, NeuroSage asks: *"What would have happened if I had clicked $Y$ instead of $X$?"*

* **Trace:** Rollback WORLD.md belief state.
* **Mutate:** Apply $do(a')$ to the DAG.
* **Evaluate:** If $R_{a'} > R_{a}$, log as a Mutation Signal for EVOLVE.md.

---
*NeuroSage: Moving AI from correlation to causation.*
