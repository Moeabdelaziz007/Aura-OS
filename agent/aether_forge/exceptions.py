"""
AetherOS Exception Hierarchy
=============================
Every failure mode has a named exception.
Retryable vs fatal errors are explicit — no guessing.
"""

from enum import Enum, auto
from typing import Any, List


class ForgeErrorType(Enum):
    NETWORK_TIMEOUT      = auto()
    RATE_LIMITED         = auto()
    API_SCHEMA_CHANGED   = auto()   # Triggers Deep Archaeology
    SERVICE_UNAVAILABLE  = auto()
    INVALID_PARAMS       = auto()
    VETO_BLOCKED         = auto()   # SOUL constitutional block
    SWARM_EXHAUSTED      = auto()   # All 5 agents failed
    INTENT_UNRESOLVED    = auto()   # Constraint solver failed
    PROOF_DISPUTED       = auto()   # Sources disagree > threshold
    TTL_EXPIRED          = auto()
    UNKNOWN              = auto()


class AetherBaseError(Exception):
    """Root of all AetherOS exceptions."""
    def __init__(
        self,
        error_type: ForgeErrorType,
        message: str,
        retryable: bool = False,
        service: str = "unknown",
        context: dict = None,
    ):
        self.error_type  = error_type
        self.retryable   = retryable
        self.service     = service
        self.context     = context or {}
        super().__init__(f"[{error_type.name}] {message}")


class NetworkError(AetherBaseError):
    def __init__(self, message: str, service: str = "unknown"):
        super().__init__(ForgeErrorType.NETWORK_TIMEOUT, message,
                         retryable=True, service=service)


class RateLimitError(AetherBaseError):
    def __init__(self, message: str, service: str, retry_after_seconds: float = 60):
        super().__init__(ForgeErrorType.RATE_LIMITED, message,
                         retryable=True, service=service,
                         context={"retry_after": retry_after_seconds})
        self.retry_after = retry_after_seconds


class APISchemaChangedError(AetherBaseError):
    """Triggers Deep Archaeology self-healing protocol."""
    def __init__(self, service: str, expected_field: str):
        super().__init__(ForgeErrorType.API_SCHEMA_CHANGED,
                         f"Schema changed for {service}: missing '{expected_field}'",
                         retryable=False, service=service,
                         context={"missing_field": expected_field})


class VetoBlockedError(AetherBaseError):
    """SOUL constitutional veto — action blocked."""
    def __init__(self, action: str, reason: str):
        super().__init__(ForgeErrorType.VETO_BLOCKED,
                         f"SOUL veto blocked '{action}': {reason}",
                         retryable=False,
                         context={"action": action, "reason": reason})


class SwarmExhaustedError(AetherBaseError):
    """All 5 race agents failed — no winner."""
    def __init__(self, service: str, agent_errors: list):
        super().__init__(ForgeErrorType.SWARM_EXHAUSTED,
                         f"All swarm agents failed for '{service}'",
                         retryable=True, service=service,
                         context={"errors": agent_errors})


class IntentUnresolvedError(AetherBaseError):
    """Constraint solver could not determine intent."""
    def __init__(self, query: str, reason: str):
        super().__init__(ForgeErrorType.INTENT_UNRESOLVED,
                         f"Cannot resolve intent for: '{query}' — {reason}",
                         retryable=False,
                         context={"query": query})


class ProofDisputedError(AetherBaseError):
    """Two sources disagree beyond acceptable threshold."""
    def __init__(self, source_a: str, val_a: Any,
                 source_b: str, val_b: Any, deviation_pct: float):
        super().__init__(ForgeErrorType.PROOF_DISPUTED,
                         f"Data disputed: {source_a}={val_a} vs {source_b}={val_b} "
                         f"({deviation_pct:.1f}% deviation)",
                         retryable=True,
                         context={"deviation_pct": deviation_pct})
