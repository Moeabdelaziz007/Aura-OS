"""
🧠 AetherOS ADK Client Library
================================
A comprehensive, production-ready wrapper for Google ADK SDK.

Features:
- Type-safe abstractions
- Connection pooling
- Authentication handling
- Retry logic with exponential backoff
- Circuit breaker pattern
- Rate limiting
- Request/Response interceptors
- Logging and telemetry
- Async/await support

Example:
    >>> from agent.aether_forge.adk_client import create_client
    >>> 
    >>> async def main():
    ...     client = create_client(
    ...         project_id="my-project",
    ...         api_key="your-api-key"
    ...     )
    ...     response = await client.list_agents()
    ...     print(response.data)
    ...     await client.close()

Author: AetherOS Team
License: MIT
"""

from __future__ import annotations

# Version
__version__ = "1.0.0"

# Import all public classes
from .client import (
    ADKClient,
    create_client,
    create_client_async
)

from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerMetrics,
    CircuitState,
    CircuitBreakerRegistry,
    get_circuit_breaker,
    reset_all_circuit_breakers
)

from .rate_limiter import (
    RateLimiter,
    RateLimitConfig,
    RateLimitMetrics,
    RateLimiterRegistry,
    get_rate_limiter,
    reset_all_rate_limiters
)

from .retry import (
    RetryPolicy,
    RetryConfig,
    RetryStrategy,
    RetryExecutor,
    RetryState,
    create_retry_executor
)

from .telemetry import (
    LogLevel,
    LogEntry,
    LogSink,
    ConsoleSink,
    FileSink,
    TelemetrySink,
    InMemoryTelemetrySink,
    AetherTelemetryHandler
)

from .types import (
    ADKConfig,
    ADKRequest,
    ADKResponse,
    ADKAgent,
    ADKSession,
    AuthCredentials,
    AuthType,
    Environment,
    InterceptorChain,
    TelemetryCallback,
    TelemetryEvent,
    PoolConfig,
    JSON
)

from .exceptions import (
    ADKException,
    ADKAuthenticationError,
    ADKAuthorizationError,
    ADKBadRequestError,
    ADKNotFoundError,
    ADKValidationError,
    ADKRateLimitError,
    ADKServerError,
    ADKTimeoutError,
    ADKConnectionError,
    ADKCircuitBreakerError,
    ADKAgentError,
    ADKAgentNotFoundError,
    ADKSessionError,
    ADKSessionNotFoundError,
    ADKErrorFactory,
    is_retryable_error,
    get_error_message
)

# All public exports
__all__ = [
    # Version
    "__version__",
    
    # Client
    "ADKClient",
    "create_client",
    "create_client_async",
    
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerMetrics",
    "CircuitState",
    "CircuitBreakerRegistry",
    "get_circuit_breaker",
    "reset_all_circuit_breakers",
    
    # Rate Limiter
    "RateLimiter",
    "RateLimitConfig",
    "RateLimitMetrics",
    "RateLimiterRegistry",
    "get_rate_limiter",
    "reset_all_rate_limiters",
    
    # Retry
    "RetryPolicy",
    "RetryConfig",
    "RetryStrategy",
    "RetryExecutor",
    "RetryState",
    "create_retry_executor",
    
    # Telemetry
    "LogLevel",
    "LogEntry",
    "LogSink",
    "ConsoleSink",
    "FileSink",
    "TelemetrySink",
    "InMemoryTelemetrySink",
    "AetherTelemetryHandler",
    
    # Types
    "ADKConfig",
    "ADKRequest",
    "ADKResponse",
    "ADKAgent",
    "ADKSession",
    "AuthCredentials",
    "AuthType",
    "Environment",
    "InterceptorChain",
    "TelemetryCallback",
    "TelemetryEvent",
    "PoolConfig",
    "JSON",
    
    # Exceptions
    "ADKException",
    "ADKAuthenticationError",
    "ADKAuthorizationError",
    "ADKBadRequestError",
    "ADKNotFoundError",
    "ADKValidationError",
    "ADKRateLimitError",
    "ADKServerError",
    "ADKTimeoutError",
    "ADKConnectionError",
    "ADKCircuitBreakerError",
    "ADKAgentError",
    "ADKAgentNotFoundError",
    "ADKSessionError",
    "ADKSessionNotFoundError",
    "ADKErrorFactory",
    "is_retryable_error",
    "get_error_message"
]
