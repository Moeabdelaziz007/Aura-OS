"""
AetherOS — Bayesian Feedback Loop
==================================
Allows the Constraint Solver to learn from mistakes.
Adjusts template weights based on forge outcomes.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .models import ResolvedIntent

logger = logging.getLogger("aether.feedback")

CALIBRATION_FILE  = Path("agent/aether_memory/CALIBRATION.json")
LEARNING_RATE      = 0.15
MIN_WEIGHT         = 0.10
MAX_WEIGHT         = 3.0


@dataclass
class AetherTemplateCalibration:
    """Learning data for each intent template."""
    template_action: str
    weight:          float = 1.0
    total_uses:       int   = 0
    correct_uses:     int   = 0
    wrong_uses:       int   = 0
    last_updated:    str   = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )

    @property
    def accuracy(self) -> float:
        if self.total_uses == 0:
            return 1.0
        return self.correct_uses / self.total_uses

    @property
    def confidence_label(self) -> str:
        if self.accuracy > 0.85:  return "🟢 HIGH"
        if self.accuracy > 0.65:  return "🟡 MED"
        return                           "🔴 LOW"


class AetherFeedbackLoop:
    """Self-improving intent calibration mechanism."""

    def __init__(self, filepath: Path = CALIBRATION_FILE):
        self._filepath     = filepath
        self._calibrations: Dict[str, AetherTemplateCalibration] = {}
        self._lock          = asyncio.Lock()
        self._load_sync()
        logger.info(f"🔄 FeedbackLoop initialized | {len(self._calibrations)} templates")

    async def record_outcome(
        self,
        intent: ResolvedIntent,
        success: bool,
        correct_action: Optional[str] = None,
    ) -> None:
        """Update weights based on success/failure of a forged intent."""
        async with self._lock:
            cal = self._get_or_create(intent.action)
            cal.total_uses += 1

            if success:
                cal.correct_uses += 1
                cal.weight = min(MAX_WEIGHT, cal.weight * (1 + LEARNING_RATE * 0.5))
                logger.debug(f"✅ Feedback: '{intent.action}' correct → weight={cal.weight:.3f}")
            else:
                cal.wrong_uses += 1
                cal.weight = max(MIN_WEIGHT, cal.weight * (1 - LEARNING_RATE))
                logger.warning(f"❌ Feedback: '{intent.action}' wrong → weight={cal.weight:.3f}")

                if correct_action and correct_action != intent.action:
                    correct_cal = self._get_or_create(correct_action)
                    correct_cal.weight = min(MAX_WEIGHT, correct_cal.weight * (1 + LEARNING_RATE))
                    logger.info(f"📈 Boosted '{correct_action}' → weight={correct_cal.weight:.3f}")

            cal.last_updated = datetime.utcnow().isoformat()
            await self._flush_atomic()

    async def get_weights(self) -> Dict[str, float]:
        async with self._lock:
            return {action: cal.weight for action, cal in self._calibrations.items()}

    async def detect_confusion(self, intent: ResolvedIntent) -> Optional[str]:
        async with self._lock:
            cal = self._calibrations.get(intent.action)
            if cal and cal.total_uses >= 5 and cal.accuracy < 0.60:
                return f"System uncertain ({cal.accuracy:.0%} accuracy on '{intent.action}'). Clarity needed."
            return None

    def _get_or_create(self, action: str) -> AetherTemplateCalibration:
        if action not in self._calibrations:
            self._calibrations[action] = AetherTemplateCalibration(template_action=action)
        return self._calibrations[action]

    async def _flush_atomic(self) -> None:
        self._filepath.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self._filepath.with_suffix(".tmp")
        data = {k: v.__dict__ for k, v in self._calibrations.items()}

        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, self._filepath)
        except Exception as e:
            logger.error(f"❌ Calibration flush failed: {e}")

    def _load_sync(self) -> None:
        if not self._filepath.exists(): return
        try:
            with open(self._filepath, encoding="utf-8") as f:
                raw = json.load(f)
            for action, v in raw.items():
                self._calibrations[action] = AetherTemplateCalibration(**v)
        except Exception as e:
            logger.warning(f"Calibration load failed: {e}")
