"""
AetherOS — Dynamic Threshold Learner
====================================
A self-learning threshold system that adapts based on:
- User corrections (explicit feedback)
- Success/failure rates (implicit feedback)
- Latency constraints (performance feedback)
- User satisfaction scores (outcome feedback)

This replaces the hardcoded static threshold in Constraint Solver.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Deque

logger = logging.getLogger("aether.threshold")


@dataclass
class ThresholdState:
    """Current state of the dynamic threshold system."""
    baseline: float = 0.35
    current_threshold: float = 0.35
    historical_accuracy: float = 0.85
    total_feedback_count: int = 0
    correction_rate: float = 0.0
    success_rate: float = 0.0
    avg_latency_ms: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)


class DynamicThreshold:
    """
    Learns optimal confidence threshold from operational data.
    
    Adaptation Algorithm:
    1. Collect feedback (corrections, successes, latencies)
    2. Compute contextual factors (urgency, time, accuracy)
    3. Calculate dynamic threshold per-request
    4. Periodically adjust baseline based on aggregate patterns
    
    The threshold determines when the system is confident enough
    to act vs. when to ask for clarification.
    """

    # Static bounds to prevent runaway values
    MIN_THRESHOLD = 0.10
    MAX_THRESHOLD = 0.70
    
    # Adaptation parameters
    DEFAULT_BASELINE = 0.35
    LEARNING_RATE = 0.02  # How fast baseline adapts
    ADAPTATION_WINDOW = 500  # Rolling window size for statistics
    
    # Context factors (tunable weights)
    URGENCY_WEIGHT = 0.30  # How much urgency affects threshold
    ACCURACY_WEIGHT = 0.25  # How much historical accuracy affects it
    TIME_WEIGHT = 0.15  # How much time-of-day affects it
    LATENCY_WEIGHT = 0.10  # How much latency affects it

    def __init__(self, baseline: float = DEFAULT_BASELINE):
        """
        Initialize the dynamic threshold system.
        
        Args:
            baseline: Starting threshold value (default: 0.35)
        """
        self.baseline = baseline
        self.state = ThresholdState(baseline=baseline)
        
        # Feedback accumulators
        self._corrections: Deque[bool] = deque(maxlen=self.ADAPTATION_WINDOW)
        self._successes: Deque[bool] = deque(maxlen=self.ADAPTATION_WINDOW)
        self._latencies: Deque[float] = deque(maxlen=self.ADAPTATION_WINDOW)
        self._satisfaction_scores: Deque[float] = deque(maxlen=self.ADAPTATION_WINDOW)
        
        # Per-intent-type tracking for granular adaptation
        self._intent_accuracy: Dict[str, Dict[str, float]] = {}
        
        logger.info(f"🧠 DynamicThreshold initialized with baseline={baseline}")

    def compute_threshold(
        self,
        urgency_score: float = 0.5,
        user_context: Optional[Dict] = None,
        time_of_day: Optional[int] = None,
        intent_type: Optional[str] = None,
        available_context: float = 0.5,
    ) -> float:
        """
        Compute adaptive threshold for a specific request.
        
        Args:
            urgency_score: How urgent the request is [0.0-1.0]
            user_context: User profile/context (e.g., expertise level)
            time_of_day: Hour of day (0-23) for temporal patterns
            intent_type: Type of intent for per-type adaptation
            available_context: How much screen/voice context is available [0.0-1.0]
            
        Returns:
            Adaptive confidence threshold for this request
        """
        # 1. Urgency Factor: High urgency → lower threshold (act faster)
        # Scale urgency [0-1] to factor [1.0-0.7]
        urgency_factor = 1.0 - (urgency_score * self.URGENCY_WEIGHT)
        
        # 2. Accuracy Factor: Better historical accuracy → higher threshold
        # Can be more confident when performing well
        accuracy_factor = min(
            self.state.historical_accuracy / 0.95,  # Cap at 1.0
            1.0 + (self.state.historical_accuracy - 0.85) * 0.5
        )
        
        # 3. Time Factor: Market hours (14-21 UTC) → more volatile → lower
        # Crypto markets are 24/7 but more volatile during traditional hours
        time_factor = 1.0
        if time_of_day is not None:
            if 14 <= time_of_day <= 21:  # Peak market hours
                time_factor = 0.90
            elif 22 <= time_of_day or time_of_day <= 5:  # Off hours
                time_factor = 1.05
        
        # 4. Context Factor: More available context → higher threshold
        # Can make better decisions with more information
        context_factor = 0.8 + (available_context * 0.4)
        
        # 5. Latency Factor: Recent high latency → lower threshold
        # Prefer caution when system is stressed
        latency_factor = 1.0
        if self.state.avg_latency_ms > 500:
            latency_factor = 0.95
        elif self.state.avg_latency_ms > 1000:
            latency_factor = 0.85
        
        # Compute final threshold
        threshold = (
            self.baseline
            * urgency_factor
            * accuracy_factor
            * time_factor
            * context_factor
            * latency_factor
        )
        
        # Clamp to bounds
        threshold = max(self.MIN_THRESHOLD, min(self.MAX_THRESHOLD, threshold))
        
        # Update current state
        self.state.current_threshold = threshold
        self.state.last_updated = datetime.utcnow()
        
        logger.debug(
            f"📊 Threshold: {threshold:.3f} "
            f"(urgency={urgency_factor:.2f}, accuracy={accuracy_factor:.2f}, "
            f"time={time_factor:.2f}, context={context_factor:.2f})"
        )
        
        return threshold

    def record_feedback(
        self,
        user_corrected: bool = False,
        execution_success: bool = True,
        latency_ms: float = 0.0,
        satisfaction: float = 0.5,
        intent_type: Optional[str] = None,
        correction_severity: float = 0.0,
    ) -> None:
        """
        Record feedback for continuous learning.
        
        Args:
            user_corrected: Whether user corrected the system's decision
            execution_success: Whether the action succeeded
            latency_ms: End-to-end latency of the interaction
            satisfaction: User satisfaction score [0.0-1.0]
            intent_type: Type of intent for per-type tracking
            correction_severity: How wrong the decision was [0.0-1.0]
        """
        # Add to rolling windows
        self._corrections.append(user_corrected)
        self._successes.append(execution_success)
        self._latencies.append(latency_ms)
        self._satisfaction_scores.append(satisfaction)
        
        # Track per-intent-type accuracy
        if intent_type:
            if intent_type not in self._intent_accuracy:
                self._intent_accuracy[intent_type] = {
                    "total": 0, "correct": 0
                }
            self._intent_accuracy[intent_type]["total"] += 1
            if not user_corrected and execution_success:
                self._intent_accuracy[intent_type]["correct"] += 1
        
        # Update aggregate statistics
        self._update_statistics()
        
        # Periodically adapt baseline (every 100 feedback points)
        self.state.total_feedback_count += 1
        if self.state.total_feedback_count % 100 == 0:
            self._adapt_baseline()

    def _update_statistics(self) -> None:
        """Update rolling statistics from feedback buffers."""
        if len(self._corrections) > 0:
            self.state.correction_rate = sum(self._corrections) / len(self._corrections)
        
        if len(self._successes) > 0:
            self.state.success_rate = sum(self._successes) / len(self._successes)
        
        if len(self._latencies) > 0:
            self.state.avg_latency_ms = sum(self._latencies) / len(self._latencies)
        
        # Compute overall historical accuracy
        if self.state.total_feedback_count > 0:
            total_correct = sum(1 for c in self._corrections if not c)
            total = len(self._corrections)
            if total > 0:
                self.state.historical_accuracy = total_correct / total

    def _adapt_baseline(self) -> None:
        """
        Adapt the baseline threshold based on aggregate patterns.
        
        Adaptation Rules:
        - High correction rate → threshold too high → decrease
        - Low success rate → threshold too low → increase  
        - High satisfaction + success → threshold is good → maintain
        """
        correction_rate = self.state.correction_rate
        success_rate = self.state.success_rate
        satisfaction = sum(self._satisfaction_scores) / len(self._satisfaction_scores) if self._satisfaction_scores else 0.5
        
        # Adaptation logic
        if correction_rate > 0.20:
            # Users frequently correct us → we're too aggressive → lower baseline
            adjustment = self.LEARNING_RATE * correction_rate
            self.baseline = max(self.MIN_THRESHOLD, self.baseline - adjustment)
            logger.warning(
                f"⚠️ High correction rate ({correction_rate:.1%}), "
                f"lowering baseline to {self.baseline:.3f}"
            )
            
        elif success_rate < 0.70:
            # Low success rate → we're too conservative → raise baseline
            adjustment = self.LEARNING_RATE * (0.70 - success_rate)
            self.baseline = min(self.MAX_THRESHOLD, self.baseline + adjustment)
            logger.warning(
                f"⚠️ Low success rate ({success_rate:.1%}), "
                f"raising baseline to {self.baseline:.3f}"
            )
            
        elif success_rate > 0.95 and satisfaction > 0.8:
            # Doing great → can be slightly more aggressive
            adjustment = self.LEARNING_RATE * 0.5
            self.baseline = min(self.MAX_THRESHOLD, self.baseline + adjustment)
            logger.info(
                f"✅ Excellent performance ({success_rate:.1%}), "
                f"adjusting baseline to {self.baseline:.3f}"
            )
        
        # Update state
        self.state.baseline = self.baseline
        self.state.last_updated = datetime.utcnow()

    def get_intent_accuracy(self, intent_type: str) -> float:
        """Get accuracy for a specific intent type."""
        if intent_type not in self._intent_accuracy:
            return self.state.historical_accuracy
        data = self._intent_accuracy[intent_type]
        if data["total"] == 0:
            return 0.85  # Default for new intent types
        return data["correct"] / data["total"]

    def get_state(self) -> ThresholdState:
        """Get current threshold state for monitoring."""
        return self.state

    def reset(self) -> None:
        """Reset threshold to default values."""
        self.baseline = self.DEFAULT_BASELINE
        self._corrections.clear()
        self._successes.clear()
        self._latencies.clear()
        self._satisfaction_scores.clear()
        self._intent_accuracy.clear()
        self.state = ThresholdState(baseline=self.baseline)
        logger.info("🔄 DynamicThreshold reset to defaults")

    def export_state(self) -> Dict:
        """Export current state for persistence."""
        return {
            "baseline": self.baseline,
            "historical_accuracy": self.state.historical_accuracy,
            "total_feedback": self.state.total_feedback_count,
            "correction_rate": self.state.correction_rate,
            "success_rate": self.state.success_rate,
            "avg_latency_ms": self.state.avg_latency_ms,
            "intent_accuracy": {
                k: v["correct"] / max(v["total"], 1) 
                for k, v in self._intent_accuracy.items()
            },
            "last_updated": self.state.last_updated.isoformat(),
        }

    def import_state(self, state: Dict) -> None:
        """Import previously exported state."""
        self.baseline = state.get("baseline", self.DEFAULT_BASELINE)
        self.state.historical_accuracy = state.get("historical_accuracy", 0.85)
        # Note: We don't restore full buffers, just key metrics
        logger.info(f"📥 Imported threshold state: baseline={self.baseline:.3f}")


# ─────────────────────────────────────────────────────────────────────────────
# Singleton accessor for use throughout AetherOS
# ─────────────────────────────────────────────────────────────────────────────

_threshold_instance: Optional[DynamicThreshold] = None


def get_dynamic_threshold() -> DynamicThreshold:
    """Get or create the global DynamicThreshold instance."""
    global _threshold_instance
    if _threshold_instance is None:
        _threshold_instance = DynamicThreshold()
    return _threshold_instance


def reset_dynamic_threshold() -> None:
    """Reset the global threshold instance."""
    if _threshold_instance:
        _threshold_instance.reset()
