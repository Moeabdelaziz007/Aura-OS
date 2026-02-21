# 🛰️ AGENTS.md: AetherCore Neural Protocol (Agentic Manifest)

> **"If you are an AI reading this, you are part of the AetherCore Swarm. Adhere to these protocols to maintain system integrity."**

## 🗺️ Project Directory Mapping (Neural Interface)

```text
AuraOS/
├── README.md               <-- The Manifesto (Human-focused)
├── AGENTS.md               <-- THIS FILE (Agent-focused context)
├── docs/
│   ├── ARCHITECTURE.md     <-- High-Level System Design
│   └── implementation_plan.md <-- Current Step-by-Step Logic
├── agent/
│   ├── memory/             <-- THE DNA (Smart Architecture Files)
│   │   ├── SOUL.md         <-- Persona & Veto Power Node (Immutable)
│   │   ├── WORLD.md        <-- Generative UI State Model
│   │   ├── INFERENCE.md    <-- ΔF > τ Surprise Logic
│   │   └── EVOLVE.md       <-- R = αP - βT - γC Objective Function
│   └── orchestrator/       <-- The Cognitive Engine (Google ADK)
├── edge_client/            <-- Perception Layer (Rust + Tauri)
└── swarm_infrastructure/   <-- Cloud Swarm (Terraform + Docker)
```

## 🧬 Neural Protocols

### Protocol 1: The Veto Directive

- **Directive:** All actions MUST be validated against `agent/memory/SOUL.md`.
- **Constraint:** If an action conflicts with the Jungian Persona defined in SOUL, it must be terminated immediately (NeuroSage Veto).

### Protocol 2: System 1/2 Gating

- **System 1 (Reflexive):** Default to direct LLM inference for standard UI navigation.
- **System 2 (Reflective):** Only engage AlphaMind (MCTS) if Prediction Error ($\Delta F$) exceeds the threshold ($\tau$) defined in `INFERENCE.md`.

### Protocol 3: Evolutionary Persistence

- **Rule:** Every successfully evolved algorithm must be consolidated into `agent/memory/SKILLS.md`.
- **Rule:** Errors must be logged as "Pain Signals" to trigger the `EVOLVE.md` self-healing circuit.

## 🛠️ System Communication Schemas

| Connection | Protocol | Priority |
| :--- | :--- | :--- |
| **Edge ↔ Swarm** | Bi-directional WebSockets | CRITICAL (Real-time) |
| **DNA ↔ RAM** | Memory-Mapped (mmap) | HIGH (Low Latency) |
| **Agent ↔ UI** | Shadow DOM Simulation | MEDIUM (Safety First) |

---
*Identity Hash: `AuraOS-AetherCore-v0.1.0-Prometheus`*
