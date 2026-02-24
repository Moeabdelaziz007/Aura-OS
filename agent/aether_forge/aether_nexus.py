"""
AetherOS — AetherNexus v2 (Async-Safe DNA Memory)
====================================================
Atomic, thread-safe persistent memory for crystallized patterns.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .models import DNAPattern

logger = logging.getLogger("aether.nexus")

NEXUS_FILE            = Path("agent/aether_memory/NEXUS.json")
ENERGY_GAIN_SUCCESS   = +10.0
ENERGY_LOSS_FAILURE   = -20.0
ENERGY_LOSS_SLOW      = -5.0
LATENCY_SLOW_MS       = 3000.0
PRUNE_THRESHOLD       = 0.0
CRYSTALLIZE_THRESHOLD = 50.0


class AetherNexus:
    """DNA memory — fully async-safe with atomic writes."""

    def __init__(self, filepath: Path = NEXUS_FILE):
        self._filepath  = filepath
        self._dna: Dict[str, DNAPattern] = {}
        self._lock      = asyncio.Lock()
        self._dirty     = False
        self._load_sync()

        logger.info(f"🧬 AetherNexus v2 initialized | {len(self._dna)} patterns")

    async def aether_recall(self, service: str) -> Optional[DNAPattern]:
        """System 1 fast-path — read with lock."""
        async with self._lock:
            pattern = self._dna.get(service)
            if pattern and pattern.is_viable():
                # We don't increment use_count here as it might be a speculative check
                return pattern
            return None

    async def aether_engrave(
        self,
        service: str,
        pattern: dict,
        success: bool,
        latency_ms: float = 0.0,
    ) -> None:
        """Update DNA pattern with atomic persist."""
        async with self._lock:
            self._update_pattern(service, pattern, success, latency_ms)
            self._prune_in_place()
            self._dirty = True
            await self._flush_atomic()

    async def aether_is_crystallized(self, service: str) -> bool:
        async with self._lock:
            p = self._dna.get(service)
            return p is not None and p.energy_credits >= CRYSTALLIZE_THRESHOLD

    def _update_pattern(
        self,
        service: str,
        pattern: dict,
        success: bool,
        latency_ms: float,
    ) -> None:
        existing = self._dna.get(service)

        if existing:
            if success:
                existing.energy_credits += ENERGY_GAIN_SUCCESS
                n = existing.use_count + 1
                existing.avg_latency_ms = (
                    existing.avg_latency_ms * existing.use_count + latency_ms
                ) / n
                existing.use_count   = n
                existing.success_rate = existing.success_rate * 0.9 + 0.1
            else:
                existing.energy_credits += ENERGY_LOSS_FAILURE
                existing.success_rate   = existing.success_rate * 0.9

            if latency_ms > LATENCY_SLOW_MS:
                existing.energy_credits += ENERGY_LOSS_SLOW

            existing.last_used = datetime.utcnow()
        else:
            self._dna[service] = DNAPattern(
                service=service,
                params_template=pattern,
                avg_latency_ms=latency_ms,
                success_rate=1.0 if success else 0.0,
                energy_credits=(ENERGY_GAIN_SUCCESS if success else ENERGY_LOSS_FAILURE),
                use_count=1,
            )

    def _prune_in_place(self) -> None:
        dead = [k for k, v in self._dna.items() if v.energy_credits <= PRUNE_THRESHOLD]
        for k in dead:
            del self._dna[k]

    async def _flush_atomic(self) -> None:
        if not self._dirty: return

        self._filepath.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self._filepath.with_suffix(".tmp")

        serializable = {
            k: {
                "service":         v.service,
                "params_template": v.params_template,
                "avg_latency_ms":  v.avg_latency_ms,
                "success_rate":    v.success_rate,
                "energy_credits":  v.energy_credits,
                "use_count":       v.use_count,
                "last_used":       v.last_used.isoformat(),
                "created_at":      v.created_at.isoformat(),
            }
            for k, v in self._dna.items()
        }

        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(serializable, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, self._filepath)
            self._dirty = False
        except Exception as e:
            logger.error(f"❌ Nexus flush failed: {e}")

    def _load_sync(self) -> None:
        if not self._filepath.exists(): return
        try:
            with open(self._filepath, encoding="utf-8") as f:
                raw = json.load(f)
            for k, v in raw.items():
                self._dna[k] = DNAPattern(
                    service=v["service"],
                    params_template=v.get("params_template", {}),
                    avg_latency_ms=v.get("avg_latency_ms", 999.0),
                    success_rate=v.get("success_rate", 0.5),
                    energy_credits=v.get("energy_credits", 0.0),
                    use_count=v.get("use_count", 0),
                    last_used=datetime.fromisoformat(v.get("last_used", datetime.utcnow().isoformat())),
                    created_at=datetime.fromisoformat(v.get("created_at", datetime.utcnow().isoformat())),
                )
        except Exception as e:
            logger.warning(f"Nexus load failed: {e}")

    async def tidal_prune(self) -> int:
        async with self._lock:
            before = len(self._dna)
            self._prune_in_place()
            pruned = before - len(self._dna)
            if pruned > 0:
                self._dirty = True
                await self._flush_atomic()
            return pruned

    async def status(self) -> dict:
        async with self._lock:
            return {
                "total_patterns": len(self._dna),
                "patterns": {k: v.energy_credits for k, v in self._dna.items()}
            }
