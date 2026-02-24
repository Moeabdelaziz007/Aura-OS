"""
AetherOS — Circuit Breaker
============================
Protects the Swarm Race from accepting corrupt or failed results.
States: CLOSED, OPEN, HALF_OPEN.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Awaitable, Callable, Dict, Optional, TypeVar

logger = logging.getLogger("aether.circuit")

T = TypeVar("T")


class CircuitState(Enum):
    CLOSED    = auto()   # Normal — all requests pass
    OPEN      = auto()   # Broken — no requests
    HALF_OPEN = auto()   # Probe — trial request


@dataclass
class CircuitStats:
    """Live stats for each service circuit memory."""
    service: str
    state: CircuitState               = CircuitState.CLOSED
    failure_count: int                 = 0
    success_count: int                 = 0
    last_failure_time: float          = 0.0
    last_state_change: float          = field(default_factory=time.monotonic)
    total_requests: int                = 0
    total_blocked: int                 = 0

    # Thresholds
    failure_threshold: int             = 3      # Open after 3 failures
    success_threshold: int             = 2      # Close after 2 successes in HALF_OPEN
    recovery_timeout_sec: float       = 30.0   # Wait 30s before HALF_OPEN

    @property
    def failure_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.failure_count / self.total_requests

    @property
    def seconds_since_last_failure(self) -> float:
        if self.last_failure_time == 0:
            return float("inf")
        return time.monotonic() - self.last_failure_time


class CircuitOpenError(Exception):
    """Raised when the circuit is OPEN."""
    def __init__(self, service: str, retry_after: float):
        self.service     = service
        self.retry_after = retry_after
        super().__init__(
            f"Circuit OPEN for '{service}'. "
            f"Retry after {retry_after:.1f}s"
        )


class AetherResponseValidator:
    """
    Validates results before they are accepted as winners.
    Prevents corrupt data from entering the forge.
    """

    REQUIRED_FIELDS: Dict[str, list] = {
        "coingecko":     ["trend_data"], # Representative field
        "github":        ["Top_Repos", "Total_Found"],
        "weather":       ["Temp", "City"],
    }

    def aether_validate(self, service: str, data: dict) -> tuple[bool, Optional[str]]:
        """Returns (is_valid, error_message)."""
        required = self.REQUIRED_FIELDS.get(service, [])
        for field_name in required:
            if field_name not in data:
                return False, f"Missing required field: '{field_name}'"
            if data[field_name] is None:
                return False, f"Field '{field_name}' is None"

        # Service-specific custom logic
        if service == "coingecko":
            # Check if at least one coin result is present
            coins = [k for k in data.keys() if k not in ("trend_data",)]
            if not coins:
                return False, "No coin data found in response"
            for coin in coins:
                if "Price_USD" not in data[coin]:
                    return False, f"Missing Price_USD for {coin}"
        
        return True, None


class AetherCircuitBreaker:
    """Manages circuit state for all AetherOS services."""

    def __init__(self):
        self._circuits: Dict[str, CircuitStats] = {}
        self._validator = AetherResponseValidator()
        self._lock = asyncio.Lock()

    def _get_or_create(self, service: str) -> CircuitStats:
        if service not in self._circuits:
            self._circuits[service] = CircuitStats(service=service)
        return self._circuits[service]

    async def call(
        self,
        service: str,
        fn: Callable[..., Awaitable[T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Wrap an async call with circuit breaker logic."""
        async with self._lock:
            stats = self._get_or_create(service)
            self._maybe_transition(stats)

        if stats.state == CircuitState.OPEN:
            stats.total_blocked += 1
            retry_after = stats.recovery_timeout_sec - stats.seconds_since_last_failure
            raise CircuitOpenError(service, max(retry_after, 0.0))

        if stats.state == CircuitState.HALF_OPEN:
            logger.info(f"🔶 Circuit HALF_OPEN for '{service}' — probing...")

        try:
            stats.total_requests += 1
            result = await fn(*args, **kwargs)

            # Check validity if possible
            data_to_validate = None
            if hasattr(result, "raw_response"):
                data_to_validate = result.raw_response
            elif isinstance(result, dict):
                data_to_validate = result

            if data_to_validate:
                is_valid, err = self._validator.aether_validate(service, data_to_validate)
                if not is_valid:
                    raise ValueError(f"Invalid response from {service}: {err}")

            async with self._lock:
                await self._record_success(stats)

            return result

        except Exception as e:
            async with self._lock:
                await self._record_failure(stats, e)
            raise

    def _maybe_transition(self, stats: CircuitStats) -> None:
        if stats.state == CircuitState.OPEN:
            if stats.seconds_since_last_failure >= stats.recovery_timeout_sec:
                stats.state           = CircuitState.HALF_OPEN
                stats.last_state_change = time.monotonic()
                logger.info(f"🔶 Circuit '{stats.service}': OPEN → HALF_OPEN")

    async def _record_success(self, stats: CircuitStats) -> None:
        stats.success_count += 1
        if stats.state == CircuitState.HALF_OPEN:
            if stats.success_count >= stats.success_threshold:
                stats.state         = CircuitState.CLOSED
                stats.failure_count = 0
                stats.success_count = 0
                logger.info(f"✅ Circuit '{stats.service}': HALF_OPEN → CLOSED")
        elif stats.state == CircuitState.CLOSED:
            stats.failure_count = max(0, stats.failure_count - 1)

    async def _record_failure(self, stats: CircuitStats, error: Exception) -> None:
        stats.failure_count   += 1
        stats.last_failure_time = time.monotonic()
        logger.warning(f"⚠️ Circuit '{stats.service}' failure ({stats.failure_count}/{stats.failure_threshold}): {error}")

        if (stats.state in (CircuitState.CLOSED, CircuitState.HALF_OPEN)
                and stats.failure_count >= stats.failure_threshold):
            stats.state           = CircuitState.OPEN
            stats.success_count   = 0
            stats.last_state_change = time.monotonic()
            logger.error(f"🔴 Circuit '{stats.service}': → OPEN")

    def status(self) -> Dict[str, dict]:
        return {
            svc: {
                "state":         s.state.name,
                "failures":      s.failure_count,
                "failure_rate":  f"{s.failure_rate:.0%}",
                "total_blocked": s.total_blocked,
                "total_requests":s.total_requests,
            }
            for svc, s in self._circuits.items()
        }

# Singleton
_breaker_instance: Optional[AetherCircuitBreaker] = None

def get_circuit_breaker() -> AetherCircuitBreaker:
    global _breaker_instance
    if _breaker_instance is None:
        _breaker_instance = AetherCircuitBreaker()
    return _breaker_instance
