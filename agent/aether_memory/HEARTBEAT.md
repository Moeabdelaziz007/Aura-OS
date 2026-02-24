# 💓 HEARTBEAT.md: AetherCore Cardiac Oscillator

```yaml
version: 0.2.0
pillar: HyperMind (Pacemaker)
status: NOMINAL
```

## 📊 Heartbeat Configuration

The cardiac oscillator drives the system with the following parameters:

| Parameter | Type | Default | Range | Purpose |
|:---|:---|:---|:---|:---|
| `pulse_interval` | integer | 1000 | [500, 5000] Milliseconds between pulses |
| `synaptic_decay_rate` | float | 0.01 | [0.001, 0.1] Decay factor for synaptic weights |
| `synaptic_reinforcement` | float | 0.1 | [0.01, 0.5] Reinforcement factor for successful actions |
| `evolution_trigger_threshold` | float | 0.3 | [0.1, 0.5] Delta F threshold for evolution |

## ⏱️ نبضات النظام

يُدفَع كل ثانية (1000ms) ويُسجل في PULSE.md وNEXUS.md تحديثات.

* يُبلغ latency العصبي، ضغط السياق، معاملات استكشاف/استغلال.
* يحدث تعديل تلقائي للـ`strength` في الـNexus synapses وفقًا لمعدل النجاح.

## 🧬 بروتوكول تنشيط التطور

عند اكتشاف خطأ أو مفاجأة (Delta F ≥ τ) تُرسل إشارة "Pain Signal" إلى
`EVOLVE.md` و`Aether-Navigator`.

```yaml
evolution_trigger:
  enabled: true
  conditions:
    - type: "error_detected"
      action: "trigger_evolve"
    - type: "surprise_exceeded"
      threshold: 0.3
      action: "trigger_evolve"
    - type: "performance_degraded"
      threshold: 0.2
      action: "trigger_evolve"
```

## 🔗 Synaptic Weight Updates

Every heartbeat updates synaptic weights in [`NEXUS.md`](agent/memory/NEXUS.md):

```yaml
synaptic_update:
  formula: "new_strength = old_strength * decay_factor + reward_signal"
  decay_factor: 0.99
  reward_signal:
    success: 0.1
    failure: -0.05
    neutral: 0.0
```

### Weight Update Logic

For each synapse in NEXUS:
1. **Decay:** Apply decay factor to reduce strength over time
2. **Reinforce:** Add reward signal based on recent action outcome
3. **Clamp:** Ensure strength stays in [0, 1] range

$$strength_{new} = \min(1.0, \max(0.0, strength_{old} \cdot 0.99 + reward))$$

## 📡 واجهة مراقبة

تدعم Heartbeat واجهة WebSocket ثانوية تبث حالة الصحة إلى لوحة مراقبة Cloud.

```yaml
monitoring_interface:
  enabled: true
  websocket_endpoint: "ws://localhost:8001/health"
  broadcast_interval: 1000
  metrics:
    - pulse_id
    - status
    - latency
    - entropy
    - context_pressure
    - synaptic_health
```

## 🔄 Heartbeat Cycle

Each heartbeat performs the following operations:

```yaml
heartbeat_cycle:
  1. collect_metrics:
      - neural_latency
      - aether_entropy
      - context_pressure
      - swarm_efficiency
  2. update_synapses:
      - apply_decay
      - apply_reinforcement
      - clamp_values
  3. check_health:
      - dna_continuity
      - cognitive_sync
      - veto_consistency
  4. broadcast_status:
      - send_to_monitoring
      - log_to_pulse_md
  5. trigger_evolution:
      - if_pain_signal_detected
      - if_surprise_exceeded
      - if_performance_degraded
```

## 📊 Synaptic Health Metrics

Health of the synaptic network is tracked:

```yaml
synaptic_health:
  total_synapses: 1000
  active_synapses: 850
  average_strength: 0.75
  weak_synapses_count: 50  # strength < 0.3
  strong_synapses_count: 300  # strength > 0.8
  last_update: 1707234567890
```

## 🚨 Heartbeat Alerts

Alerts are generated when heartbeat detects issues:

```yaml
heartbeat_alerts:
  - type: "missed_pulse"
    threshold: 3  # consecutive missed pulses
    severity: CRITICAL
  - type: "synaptic_degradation"
    threshold: 0.5  # average strength below this
    severity: WARNING
  - type: "entropy_spike"
    threshold: 0.4
    severity: WARNING
  - type: "evolution_loop"
    threshold: 5  # consecutive evolution triggers
    severity: INFO
```

---
*القلب ينبض؛ والوَعي يستمر.*
