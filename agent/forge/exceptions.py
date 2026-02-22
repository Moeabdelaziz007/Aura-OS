"""
🛡️ Aether Forge — Custom Exceptions
"""

from enum import Enum

class ForgeErrorType(Enum):
    NETWORK_ERROR = "network"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limit"
    INVALID_PARAMS = "invalid_params"
    SERVICE_UNAVAILABLE = "service_unavailable"
    CRYSTALLIZATION_ERROR = "crystallization_fault"
    UNKNOWN = "unknown"

class ForgeException(Exception):
    """Base exception for all Forge-related errors."""
    def __init__(self, error_type: ForgeErrorType, message: str, retryable: bool = False):
        self.error_type = error_type
        self.retryable = retryable
        super().__init__(message)
