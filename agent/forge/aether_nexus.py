"""
AetherOS — AetherNexus DNA Memory
====================================
Persistent, evolutionary memory system.
Patterns that work gain energy. Patterns that fail lose it.
Low-energy patterns are pruned (Digital Darwinism).
Successful patterns crystallize into System 1 fast-path.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from .models import DNAPattern

logger = logging.getLogger("aether.nexus")

NEXUS_FILE = Path("agent/memory/NEXUS.json")

ENERGY_GAIN_SUCCESS  = +10.0
ENERGY_LOSS_FAILURE  = -20.0
ENERGY_LOSS_SLOW     = -5.0
LATENCY_SLOW_MS      = 3000.0
PRUNE_THRESHOLD      = 0.0
CRYSTALLIZE_THRESHOLD = 50.0   # Energy needed for System 1 fast-path


class AetherNexus:
    """
    The DNA memory of AetherOS.
    JSON-backed, energy-based, self-pruning.
    """

    def __init__(self, filepath: Path = NEXUS_FILE):
        self._filepath = filepath
        self._dna: Dict[str, DNAPattern] = {}
        self._load()
        logger.info(f"🧬 AetherNexus initialized ({len(self._dna)} patterns)")

    def recall(self, service: str) -> Optional[DNAPattern]:
        """System 1 fast-path: retrieve crystallized pattern."""
        pattern = self._dna.get(service)
        if pattern and pattern.is_viable():
            pattern.use_count += 1
            pattern.last_used = datetime.utcnow()
            return pattern
        return None

    def engrave(
        self,
        service: str,
        pattern: dict,
        success: bool,
        latency_ms: float = 0.0,
    ) -> None:
        """Update DNA after each forge cycle."""
        existing = self._dna.get(service)

        if existing:
            # Update energy
            if success:
                existing.energy_credits += ENERGY_GAIN_SUCCESS
                # Update rolling average latency
                n = existing.use_count + 1
                existing.avg_latency_ms = (
                    (existing.avg_latency_ms * existing.use_count + latency_ms) / n
                )
                existing.use_count = n
                # Update success rate
                existing.success_rate = (
                    existing.success_rate * 0.9 + 0.1
                )
            else:
                existing.energy_credits += ENERGY_LOSS_FAILURE
                existing.success_rate = existing.success_rate * 0.9

            # Slow response penalty
            if latency_ms > LATENCY_SLOW_MS:
                existing.energy_credits += ENERGY_LOSS_SLOW

            existing.last_used = datetime.utcnow()
        else:
            # New pattern
            self._dna[service] = DNAPattern(
                service=service,
                params_template=pattern,
                avg_latency_ms=latency_ms,
                success_rate=1.0 if success else 0.0,
                energy_credits=ENERGY_GAIN_SUCCESS if success else ENERGY_LOSS_FAILURE,
            )

        self.tidal_prune()
        self._save()

    def tidal_prune(self) -> int:
        """Remove dead patterns. Returns count of pruned patterns."""
        before = len(self._dna)
        self._dna = {
            k: v for k, v in self._dna.items()
            if v.energy_credits > PRUNE_THRESHOLD
        }
        pruned = before - len(self._dna)
        if pruned > 0:
            logger.info(f"🌊 Tidal prune: removed {pruned} dead patterns")
        return pruned

    def is_crystallized(self, service: str) -> bool:
        """Check if pattern has enough energy for System 1 fast-path."""
        p = self._dna.get(service)
        return p is not None and p.energy_credits >= CRYSTALLIZE_THRESHOLD

    def top_performers(self, n: int = 3) -> List[DNAPattern]:
        """Get top N patterns by energy — for future Evolution Arena."""
        return sorted(
            self._dna.values(),
            key=lambda p: p.energy_credits,
            reverse=True,
        )[:n]

    def status(self) -> dict:
        return {
            "total_patterns": len(self._dna),
            "crystallized": sum(
                1 for p in self._dna.values()
                if p.energy_credits >= CRYSTALLIZE_THRESHOLD
            ),
            "patterns": {
                k: {
                    "energy": round(v.energy_credits, 1),
                    "success_rate": round(v.success_rate, 2),
                    "avg_latency_ms": round(v.avg_latency_ms, 1),
                    "use_count": v.use_count,
                }
                for k, v in self._dna.items()
            }
        }

    def _load(self) -> None:
        if not self._filepath.exists():
            self._dna = {}
            return
        try:
            with open(self._filepath) as f:
                raw = json.load(f)
            for k, v in raw.items():
                self._dna[k] = DNAPattern(
                    service=v["service"],
                    params_template=v.get("params_template", {}),
                    avg_latency_ms=v.get("avg_latency_ms", 999.0),
                    success_rate=v.get("success_rate", 0.5),
                    energy_credits=v.get("energy_credits", 0.0),
                    use_count=v.get("use_count", 0),
                    last_used=datetime.fromisoformat(
                        v.get("last_used", datetime.utcnow().isoformat())
                    ),
                )
        except Exception as e:
            logger.warning(f"Failed to load Nexus: {e} — starting fresh")
            self._dna = {}

    def _save(self) -> None:
        self._filepath.parent.mkdir(parents=True, exist_ok=True)
        serializable = {
            k: {
                "service": v.service,
                "params_template": v.params_template,
                "avg_latency_ms": v.avg_latency_ms,
                "success_rate": v.success_rate,
                "energy_credits": v.energy_credits,
                "use_count": v.use_count,
                "last_used": v.last_used.isoformat(),
                "created_at": v.created_at.isoformat(),
            }
            for k, v in self._dna.items()
        }
        with open(self._filepath, "w") as f:
            json.dump(serializable, f, indent=2, ensure_ascii=False)
