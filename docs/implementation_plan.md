# Strategic Plan: AlphaEvolve & Roadmap 2.0

Upgrade AuraOS from a static agent to a self-healing, expert-grade OS with recursive optimization.

## Proposed Changes

### [AetherCore DNA Layer]

#### [MODIFY] [EVOLVE.md](agent/memory/EVOLVE.md)
*   Inject the mathematical reward function $R = \alpha \cdot P(Success) - \beta \cdot T_{exec} - \gamma \cdot C_{code}$.
*   Define the "Self-Healing Circuit" steps.

#### [MODIFY] [README.md](README.md)
*   Integrate the "Self-Healing Engine" description into the AlphaEvolve section.
*   Update the Roadmap section to the Expert Grade 5-Phase version.

### [Engineering Layer]

* **Shadow DOM:** Plan the development of a lightweight UI cloner for Swarm simulation to avoid State Corruption.
* **System 1/2 Switch:** Implement ΔF calculation logic to gate complex reasoning.
* **mmap DNA:** Strategy for ram-speed Markdown access in Rust.


### [NEW] [CREATE] [NEXUS.md](agent/memory/NEXUS.md)
* Define the Multimodal Graph Schema with synapses linking text, visual-latent and auditory-affect.
* Implement synaptic weighting decays/strengthens tied to HEARTBEAT cycles.

### [REFAC] `agent/orchestrator/memory_parser.py` -> AuraNavigator
* Rename and add Nexus search API (search_nexus).
* Used by Gemini Live and HyperMindRouter before gating.

### [NEW] [CREATE] [HEARTBEAT.md](agent/memory/HEARTBEAT.md)
* Maintain low-latency health metrics and trigger pulse-based weight updates.

### [IMPROVE] [EVOLVE.md]
* Add Aura-Consolidation rules linking working memory to permanent synapses.
* Promote frequently used skills to Native-Aura-Skills.

## Verification Plan

### Automated Tests

* **Audit Script:** `scripts/check_dna_health.py` to verify consistency of Smart Files.
* **Evolution Test:** Simulated failure scenario to trigger AlphaEvolve healing loop.
