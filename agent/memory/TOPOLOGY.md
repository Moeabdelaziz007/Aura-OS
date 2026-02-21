# 🕸️ TOPOLOGY.md: Hypergraph Multi-Agent Data Contracts

```yaml
version: 0.1.0
pillar: HyperMind (Coordination)
graph_type: Dynamic_Directed_Hypergraph
```

## 🧬 Hyperedge Definition

Instead of linear message passing (A -> B), AuraOS agents share state via "Hyperedges" (shared context clusters):

```yaml
hyperedges:
  CONTEXT_VISUAL:
    agents: [Vision_Expert, MCTS_Navigator, SOUL]
    shared_data: [Screenshot_Buffer, Node_Map, Persona_Constraints]
    
  CONTEXT_LOGIC:
    agents: [Reasoning_Core, NeuroSage, Logic_Critic]
    shared_data: [Causal_Graphs, Prediction_History, Action_Draft]
    
  CONTEXT_EXECUTION:
    agents: [Action_Executor, Swarm_Controller, Anomaly_Sensor]
    shared_data: [Execution_Logs, Runtime_Metrics, Reward_Signal]
```

## 📡 Data Contract: Zero-Overhead Token Streaming

* **Global Context Window:** Shared via cached memory-mapped (mmap) markers.
* **Delta-Only Updates:** Direct LLM calls only consume changed state (Deltas), not the full DOM.
* **Veto Priority:** SOUL node has absolute write priority on all hyperedges.

---
*Static hierarchy is dead. Fluid hypergraph topology is the future of agentic speed.*
