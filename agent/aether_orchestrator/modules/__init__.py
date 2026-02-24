"""
AetherOS Orchestrator Modules Package

This package contains modularized components of the AetherOS orchestrator,
split from main.py for better maintainability and separation of concerns.

Modules:
- agent_manager: Agent lifecycle management (boot, shutdown, monitoring)
- task_executor: Task execution and websocket handling logic
- memory_handler: Memory operations and signal management
- telemetry_handler: Telemetry and anomaly monitoring
- api_client: API client operations and integrations
"""

from .agent_manager import AgentManager
from .task_executor import TaskExecutor
from .memory_handler import MemoryHandler
from .telemetry_handler import TelemetryHandler
from .api_client import APIClient

__all__ = [
    "AgentManager",
    "TaskExecutor",
    "MemoryHandler",
    "TelemetryHandler",
    "APIClient",
]
