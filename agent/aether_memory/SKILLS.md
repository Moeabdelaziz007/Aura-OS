# 🛠️ SKILLS.md: Executable Tool Registry (Gemini Live Contract)

```yaml
version: 1.1.0
pillar: NeuroSage (Action Space)
contract_type: Google_GenAI_Function_Declaration
```

## 📊 Skill Performance Metrics

Each tool is tracked with the following metrics to enable adaptive learning and automatic promotion:

| Metric | Type | Range | Purpose |
|:---|:---|:---|:---|
| `proficiency_score` | float | [0, 1] | Success rate of the tool (higher = more reliable) |
| `usage_count` | integer | ≥ 0 | Total number of times the tool has been used |
| `last_success_rate` | float | [0, 1] | Success rate in the last 10 executions |
| `category` | enum | UI, Filesystem, Network, Audio/Video, Shell | Grouping for intelligent selection |
| `fallback_tools` | list | tool_ids | Alternative tools to try on failure |
| `avg_latency_ms` | integer | ≥ 0 | Average execution time in milliseconds |

## 🔄 Skill Promotion Rules

A skill is automatically promoted from **System 2** to **System 1** when:
1. `proficiency_score` ≥ 0.90
2. `usage_count` ≥ 50
3. `last_success_rate` ≥ 0.95
4. `avg_latency_ms` < 150

Skills promoted to System 1 are moved to the **Native-Aether-Skills** section for reflexive execution.

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
performance_metrics:
  proficiency_score: 0.92
  usage_count: 1543
  last_success_rate: 0.95
  category: UI
  fallback_tools: [visual_coordinate_click]
  avg_latency_ms: 120
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
performance_metrics:
  proficiency_score: 0.85
  usage_count: 234
  last_success_rate: 0.88
  category: Network
  fallback_tools: []
  avg_latency_ms: 2500
```

### 🖥️ `shell_execute` (System 1/2)

Standardized bash execution for OS-level automation (ClawHub compatible).

```yaml
function_declaration:
  name: shell_execute
  description: Executes a bash command in a persistent shell session.
  parameters:
    type: object
    properties:
      command:
        type: string
        description: The bash command to execute (e.g., 'ls -la', 'python script.py').
    required: [command]
performance_metrics:
  proficiency_score: 0.90
  usage_count: 892
  last_success_rate: 0.93
  category: Shell
  fallback_tools: []
  avg_latency_ms: 280
```

### 📁 `filesystem_manage` (System 1)

Atomic file operations with path validation.

```yaml
function_declaration:
  name: filesystem_manage
  description: Manages local file system operations.
  parameters:
    type: object
    properties:
      operation:
        type: string
        enum: [READ, WRITE, APPEND, LIST, DELETE, SEARCH]
        description: The file operation to perform.
      path:
        type: string
        description: Absolute path to the target file/directory.
      content:
        type: string
        description: Data to write or append (optional).
    required: [operation, path]
performance_metrics:
  proficiency_score: 0.95
  usage_count: 2105
  last_success_rate: 0.97
  category: Filesystem
  fallback_tools: []
  avg_latency_ms: 95
```

### 🔍 `knowledge_search` (System 2)

Web-scale information retrieval for fact-checking and documentation.

```yaml
function_declaration:
  name: knowledge_search
  description: Performs a web search to retrieve real-time information or documentation.
  parameters:
    type: object
    properties:
      query:
        type: string
        description: The search query to execute.
      domain_bias:
        type: string
        description: Optional domain to prioritize (e.g., 'docs.python.org').
    required: [query]
performance_metrics:
  proficiency_score: 0.88
  usage_count: 456
  last_success_rate: 0.91
  category: Network
  fallback_tools: []
  avg_latency_ms: 1850
```

### 📽️ `analyze_temporal_video_delta` (System 2)

Analyzes a sequence of frames to understand temporal actions (e.g., animations, drag-and-drop).

```yaml
function_declaration:
  name: analyze_temporal_video_delta
  description: Analyzes multiple video frames to detect motion, state transitions, or temporal UI patterns.
  parameters:
    type: object
    properties:
      frames_count:
        type: integer
        description: Number of recent frames to analyze (max 30).
      objective:
        type: string
        description: Specifically what to look for (e.g., 'detect drag completion').
    required: [frames_count]
performance_metrics:
  proficiency_score: 0.82
  usage_count: 178
  last_success_rate: 0.85
  category: Audio/Video
  fallback_tools: []
  avg_latency_ms: 1200
```

### 🎯 `visual_coordinate_click` (System 1)

Precision interaction based strictly on visual computer-vision bounding boxes.

```yaml
function_declaration:
  name: visual_coordinate_click
  description: Executes a click based on visual semantic analysis, bypassing DOM tree complexity.
  parameters:
    type: object
    properties:
      target_description:
        type: string
        description: Semantic description of the element to click (e.g., 'the blue submit button').
      visual_context:
        type: string
        description: Descriptive context of the surrounding area to ensure precision.
    required: [target_description]
performance_metrics:
  proficiency_score: 0.89
  usage_count: 634
  last_success_rate: 0.92
  category: UI
  fallback_tools: [execute_ui_action]
  avg_latency_ms: 135
```

### 🗣️ `extract_vocal_sentiment` (System 1)

Real-time analysis of the user's emotional tone to adjust cognitive gating.

```yaml
function_declaration:
  name: extract_vocal_sentiment
  description: Analyzes raw PCM audio to determine user sentiment, urgency, and frustration.
  parameters:
    type: object
    properties:
      audio_segment_id:
        type: string
        description: Reference to the buffered audio chunk.
    required: [audio_segment_id]
performance_metrics:
  proficiency_score: 0.87
  usage_count: 423
  last_success_rate: 0.90
  category: Audio/Video
  fallback_tools: []
  avg_latency_ms: 80
```

### 🎙️ `synthesize_contextual_voice` (System 1)

Generates an audio response with specific emotional inflection.

```yaml
function_declaration:
  name: synthesize_contextual_voice
  description: Replies to the user with a synthesized voice mirroring their current state.
  parameters:
    type: object
    properties:
      text:
        type: string
        description: The content to speak.
      emotion:
        type: string
        enum: [CALM, URGENT, EMPATHETIC, PROFESSIONAL]
        description: The emotional tone of the voice.
      speed:
        type: number
        description: Playback speed (0.8 to 1.5).
    required: [text, emotion]
performance_metrics:
  proficiency_score: 0.91
  usage_count: 567
  last_success_rate: 0.94
  category: Audio/Video
  fallback_tools: []
  avg_latency_ms: 200
```

---
*SKILLS.md is the executable muscle of the AetherCore.*
