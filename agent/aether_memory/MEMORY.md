# 🧠 MEMORY.md: Smart Multimodal Brain (Spatio-Temporal)

```yaml
version: 1.0.0
pillar: Prometheus (Memory Engine)
model: Multimodal_Episodic_Latent_Embeddings
```

## 🎞️ Episodic Memory (Latent Stream)

AetherOS does not store raw binary blobs. It persists "Multimodal Latent Embeddings" ($z_{episodic}$) that unify disparate sensory streams into a single vector of experience.

### 🧬 Structure of an Event ($E$)

Each episodic entry is a triple $E = \langle Z_{visual}, Z_{audio}, A_{action} \rangle$:

* **$Z_{visual}$**: Compressed latent frame (128-dim) representing the UI state.
* **$Z_{audio}$**: Latent embedding of the user's vocal intent, sentiment, and ambient context.
* **$A_{action}$**: The executable tool/action taken during this state.

## 👁️ Visual Memory Retrieval

To minimize VFE ($F$), the agent constantly compares the **Live Video Delta** against its library of $Z_{visual}$ embeddings:

1. **Phase 1 (Similarity Search):** Cosine similarity check between $z_{live}$ and $z_{history}$.
2. **Phase 2 (Prediction Alignment):** If $z_{live} \approx z_{history}$, pre-load the successful $A_{action}$ into System 1 (Reflex).
3. **Phase 3 (Temporal Continuity):** Track the movement of $z$ over $N$ frames to identify UI animations vs. state changes.

## 👂 Acoustic Working Memory (A-WMB)

A high-speed, 60-second sliding window buffer that monitors the user's emotional state:

| Metric | Target | Adjustment Mechanism |
| :--- | :--- | :--- |
| **Urgency** | float [0, 1] | High Urgency -> Reduce $\tau$ (tau) -> Force System 1 Reflex. |
| **Frustration** | float [0, 1] | High Frustration -> Increase Verbosity -> Explain Reasoning (System 2). |
| **Sentiment** | float [-1, 1] | Adaptive Soul alignment based on tone. |

## 📐 Retrieval Mechanics

Memory retrieval is triggered by **Cognitive Gravity**:

* States with low $F$ (Free Energy) have higher "gravitational pull", meaning the agent reflexively defaults to what it *knows* works.
* Discovery of new $z$ states triggers the `EVOLVE.md` protocol to forge new memory nodes.

## 🧹 Memory Consolidation & Folding [REVERSE ENG #2]

To prevent **Context Window Collapse** in Gemini 3.1 Pro, AetherOS executes the **Folding Protocol**:

1. **Trigger:** Task completion signal from `HEARTBEAT.md` OR Context Pressure > 80%.
2. **Extraction:** The agent generates a "Semantic Vector Summary" ($S_{summary}$) of the task trajectory.
3. **Purge:** All raw $Z_{visual}$ (pixel-based embeddings) associated with the task are deleted from Working Memory.
4. **Compression:** The $S_{summary}$ is committed to Semantic Memory (DNA) as a high-density text object, preserving "Meaning" while liberating context window space.

---
*MEMORY.md: We do not remember what we saw; we remember what it meant ($z$).*
