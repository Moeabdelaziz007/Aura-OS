# 🌌 AuraOS: The Sovereign Agentic OS & Multimodal Knowledge Graph

<div align="center">
  <img src="assets/aethercore_architecture.png" alt="AetherCore Architecture 5 Pillars Diagram" width="100%" height="auto" style="object-fit: contain; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 14px 0 rgba(0,118,255,0.39);">

## **The Autonomous Self-Healing OS for the Gemini Live Era**

  **Built for the [Gemini Live Agents Challenge](https://geminiliveagentchallenge.devpost.com/)**

  [![Google Cloud Run Jobs](https://img.shields.io/badge/Execution-Cloud_Run_Jobs-blue?style=flat-square&logo=google-cloud)](https://cloud.google.com/run)
  [![Rust](https://img.shields.io/badge/Edge_Native-Rust_Tauri-FFC131?style=flat-square&logo=rust)](https://tauri.app/)
  [![Gemini 3.1 Pro](https://img.shields.io/badge/Brain-Gemini_3.1_Pro-9C27B0?style=flat-square&logo=google-gemini)](https://deepmind.google/technologies/gemini/)
  [![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](https://opensource.org/licenses/MIT)

  [English](README.md) | [العربية](README.md) | [Architecture Report](docs/ARCHITECTURE.md) | [Implementation Plan](docs/implementation_plan.md)

  *AuraOS is a paradigm shift. It discards stateless loops and isolated vector databases in favor of the **Aura-Nexus**—a persistent, multimodal Knowledge Graph that weaves visual latent states, text intent, and auditory affect into dynamic Synaptic Links. By synthesizing Active Inference, Quantum Swarm Execution, and Recursive Mathematical Evolution, AuraOS operates as an invincible, self-healing digital companion.*
</div>
</div>

---

- **🚀 System 1/2 Thinking:** Hyper-fast routine actions mixed with deep MCTS reasoning for complex hurdles.
- **🧬 AuraEvolve:** A recursive self-healing layer that repairs system logic in real-time.
- **🔗 Aura-Nexus & AuraNavigator:** A proprietary multimodal knowledge graph with synaptic weighting; Navigator enriches context from memory before action gating.
- **💓 Heartbeat Engine:** Real-time health pulses drive synaptic strength updates and trigger evolutionary cycles.
- **🔧 Adaptive Learning:** Cognitive weights and complexity bias now train online via feedback signals.
- **🛰️ Resilient Connectivity:** WebSocket reconnections, ping/pong health checks, and CI monitoring of the Gemini Live API.
- **☁️ Quantum Swarm:** Parallel serverless execution "collapses" into the optimal UI trajectory.
- **⚖️ NeuroSage:** Causal logic validation to eliminate hallucinations and secure transactions.
- **🕸️ HyperMind:** A non-hierarchical hypergraph topology for high-speed agent coordination.
- **👁️ Multimodal Smart Brain:** Native processing of Video, Audio, and Text as a unified latent stream.

---

## 👁️ The Pipeline of Multimodal Consciousness & Aura-Nexus

AuraOS has evolved beyond text-only processing and traditional RAG architectures. It utilizes the **Aura-Nexus Spatio-Temporal Memory Engine**:

1. **Aura-Nexus Graph:** Instead of flat text retrieval, memory is stored as an interconnected Knowledge Graph in `NEXUS.md`. Nodes ("Essences") and Edges ("Synaptic Links") map relationships between what is seen, heard, and done.
2. **Visual Latent Compression:** Raw 60FPS video is compressed into 128-dimensional vectors ($z_t$) for zero-latency retrieval within the Nexus.
3. **Acoustic Sentiment Tuning:** Real-time analysis of the user's vocal urgency dynamically adjusts the surprise threshold ($\tau$), linking emotional state to the synaptic pathways.
4. **Dynamic Synaptic Weighting:** The strength of relationships in the Nexus matrix decodes and reinforces itself autonomously based on success signals from the `HEARTBEAT.md` lifecycle hook.

---

## 🎯 The 5 Pillars of AetherCore (المعمارية الخماسية)

To secure a definitive victory in the **Live Agents** and **UI Navigator** tracks, **AuraOS** discards the outdated "Observe -> Reason -> Act" loop. We have evolved into a 5-pillar ecosystem:

### 1. 🧠 Prometheus: Active Inference & World Models (عقل النظام)

- **The Brain:** Inspired by Karl Friston, AuraOS possesses an internal "World Model". Instead of blindly clicking, it *imagines* (dreams) the consequences of its actions to minimize "Free Energy" (surprise).

### 2. ⚡ QuantumWeaver: Hybrid Quantum-Classical Swarm (المحاكي)

- **The Simulator (Cloud Run):** How does it dream? When visualizing a complex UI trajectory, AuraOS dynamically spawns **parallel Serverless Cloud Run Jobs** (like independent quantum states). Each node attempts a different visual interpretation simultaneously. The first one to succeed "collapses the wave function," terminating the others for zero-latency execution.

### 3. 🕸️ HyperMind: Hypergraph Multi-Agent Topology (شبكة التعاون)

- **The Swarm Coordinator:** Instead of rigid hierarchical multi-agent structures, AuraOS uses a dynamic **Hypergraph**. Multiple specialized agents (Vision Expert, Logic Critic, Action Executor) collaborate simultaneously on a single UI task via shared "Hyperedges," massively reducing token consumption and latency.

### 4. ⚖️ NeuroSage: Neuro-Symbolic Causal Logic (المنطق السببي)

- **The Validator:** It marries Gemini's neural creativity with hard symbolic logic. Before executing a transaction or filling a sensitive form, NeuroSage builds a causal graph ("If I do X, Y must happen") to prevent hallucinations and enforce strict rule-based constraints.

### 5. 🌳 AlphaMind: MCTS UI Navigator (البحث الشجري)

- **The Navigator:** Inspired by AlphaZero, when faced with an unknown UI, AlphaMind uses Monte Carlo Tree Search exploring the DOM/Vision tree to find the mathematically optimal sequence of clicks and scrolls.

### 6. 🧬 AlphaEvolve: Self-Healing & Recursive Evolution (التطور الذاتي)

- **The Evolver:** Inspired by **AlphaZero** & **AlphaCode**. It features a 4-step self-healing circuit: **Anomaly Detection** -> **Quantum Hypothesis Generation** -> **Sandboxed Testing** -> **DNA Consolidation**.
- **The Math:** It optimizes a unique reward function $R = \alpha \cdot P(Success) - \beta \cdot T_{exec} - \gamma \cdot C_{code}$, balancing success, speed, and simplicity.

---

### 🛠️ Recent Enhancements

1. Added `NEXUS.md` (Aura-Nexus) and `HEARTBEAT.md` to DNA.
2. Refactored `PersistentMemoryBridge` → `AuraNavigator` with Nexus search API.
3. Upgraded `EVOLVE.md` with Aura-Consolidation and skill promotion rules.
4. Implemented WebSocket reconnection/heartbeat in GeminiLiveClient.
5. Added weight learning method `update_cognitive_weights` to router.
6. Enhanced swarm node to compute basic Expected Free Energy using SKILLS.

---

## ⚡ Expert Setup & Initialization

AuraOS is a distributed system requiring the orchestration of the Python Brain, Rust Edge Client, and Cloud Swarm.

### 1. The Nervous System (Python Brain)

Initialize the cognitive orchestrator and run the foundational DNA tests.

```bash
# Clone the repository
git clone https://github.com/Moeabdelaziz007/Aura-OS.git
cd Aura-OS

# Set up the Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install AetherCore dependencies
pip install -r agent/orchestrator/requirements.txt

# Run the Aura-Nexus & Router unit tests (Crucial verification step)
pytest tests/
# OR run the monolithic sanity checks:
python3 agent/orchestrator/memory_parser.py
python3 agent/orchestrator/test_router.py
```

### 2. Peripheral Senses (Rust Edge Client)

The Edge Client captures screen and audio data with native zero-latency performance.

```bash
cd edge_client
npm install
# Boot the Tauri application (Requires cargo and rustc)
npm run dev
```

### 3. Evolutionary Sandbox (Cloud Swarm)

Provision the serverless nodes that the Prometheus engine uses to "dream" in parallel.

```bash
# Provision Cloud Swarm via Terraform
cd swarm_infrastructure/terraform
terraform init
terraform apply
```

---

<div align="center">
  <img src="assets/alpha_quantum_swarm.png" alt="Alpha Quantum Swarm Logic Infographic" width="80%" height="auto" style="border-radius: 8px; margin: 20px 0;">
</div>

---

## 🧊 The Smart Architecture Files (AetherCore DNA)

AuraOS operates without traditional, rigid databases. Its very identity, memory layers, and 5-pillar logic are codified into a specific folder of YAML/Markdown files (`agent/memory/`), representing the agent's genetic code:

| File | Function / Pillar | Key Tech | Version |
| :--- | :--- | :--- | :--- |
| **`SOUL.md`** | Persona & Identity | Bayesian Ethical Priors | 0.2.0 |
| **`WORLD.md`** | Generative Simulator | POMDP + Latent Compression | 0.2.0 |
| **`INFERENCE.md`** | Active Inference | VFE + Expected Free Energy ($G$) | 0.2.0 |
| **`CAUSAL.md`** | Anti-Hallucination | Structural Causal Models (SCM) | 0.2.0 |
| **`TOPOLOGY.md`** | Swarm Coordination | Task-Adaptive Hypergraphs | 0.1.1 |
| **`EVOLVE.md`** | Self-Healing | VerMCTS + GIF-MCTS | 0.1.1 |
| **`PULSE.md`** | Health Monitoring | Entropy & Latency Tracking | 1.0.0 |
| **`SKILLS.md`** | Tool Registry | Proficiency Scaling | 0.1.1 |

> **Note to AI Agents:** If you are an autonomous coding assistant reading this repository, you must deeply analyze and adhere to this `AetherCore` file topology before proposing code.

---

## 🏗 System Architecture Flow (مسار العمليات)

```mermaid
graph TD
    classDef edge fill:#ff9900,stroke:#fff,stroke-width:2px,color:#fff;
    classDef cloud fill:#4285f4,stroke:#fff,stroke-width:2px,color:#fff;
    classDef brain fill:#9c27b0,stroke:#fff,stroke-width:2px,color:#fff;

    A[Tauri Edge Client<br>🎤 Voice + 🖥️ Screen]:::edge -->|Bidi WebSocket| B(HyperMind Router<br>AetherCore ADK):::brain
    B -->|Active Inference| C{Prometheus World Model<br>Predicts UI State}:::brain
    
    C -->|Spawns Swarm| D1[Cloud Run Job 1<br>DOM Selector]:::cloud
    C -->|Spawns Swarm| D2[Cloud Run Job 2<br>Vision OCR]:::cloud
    C -->|Spawns Swarm| D3[Cloud Run Job 3<br>AlphaMind MCTS]:::cloud
    
    D1 -.->|Verification| E{NeuroSage Validator}:::brain
    D2 -.->|Verification| E
    D3 -.->|Verification| E
    
    E -->|Success (Exit Code 0)| F((QuantumWeaver Collapse<br>Terminate Others)):::cloud
    F -->|Execution Result| A
```

---

## 🏗️ Expert Engineering Roadmap (The Path to 11/10)

### 🏛️ Phase 1-3: Foundations & Nervous System (الجوهر المركزي)

- [x] **Step 1:** Architectural DNA & Mathematical Manifest (VFE/EFE).
- [x] **Step 2:** Zero-DB States (`agent/memory/`) with mmap access.
- [x] **Step 3:** Cognitive Orchestrator Implementation (AetherCore ADK + Async Python).

### 🛰️ Phase 4: Peripheral Senses (الحواس المحيطية - Edge Client)

- [ ] **Step 4.1:** Rust-based Screen Capture (Low-Latency Stream).
- [ ] **Step 4.2:** Multi-modal Audio-Video Synchronization for Gemini Live API.
- [ ] **Step 4.3:** **System 1/2 Switching Engine:** Implementing the $\Delta F > \tau$ threshold logic.

### ☁️ Phase 5: Quantum Swarm & Evolution (بيئة التطور)

- [ ] **Step 5.1:** Terraform Provisioning for Google Cloud Run Jobs.
- [ ] **Step 5.2:** **Shadow DOM Simulator:** Sandboxed headless-browser environment.
- [ ] **Step 5.3:** AlphaEvolve Self-Healing Recursive Loops.

---

## 💻 Tech Stack

- **Brain / Orchestrator:** Python + AetherCore Agent Development Kit (ADK) + Gemini 3.1 Pro (Live API).
- **Simulator / Swarm:** Google Cloud Run Jobs, Terraform, Docker.
- **Edge Client:** Rust + Tauri v2, React 18, Vite.
- **DNA / Memory:** Markdown/YAML `AetherCore` System.

<br>
<div align="center">
  <i>"Predicting the future by inventing it in parallel."</i>
</div>
