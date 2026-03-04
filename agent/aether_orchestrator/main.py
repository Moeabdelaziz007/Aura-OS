"""
AetherOS Orchestrator - Main Entry Point

The main asynchronous event loop for AetherOS.
Bridges the Edge Client (Sensory) via WebSockets to the DNA Brain.

This module has been refactored to use modular components for better maintainability.
"""

import asyncio
import os
import websockets
from dotenv import load_dotenv

load_dotenv()
from typing import Any, Dict

from pydantic import BaseModel, Field, ValidationError
from agent.aether_orchestrator.memory_parser import AetherNavigator
from agent.aether_orchestrator.cognitive_router import HyperMindRouter
from agent.aether_orchestrator.aether_evolve import monitor, evolve_engine
from agent.aether_forge.aether_forge import AetherForge
from agent.aether_forge.constraint_solver import MemorySignal
from agent.aether_forge.models import ForgeResult

# Import modularized components
from agent.aether_orchestrator.modules.agent_manager import AgentManager
from agent.aether_orchestrator.modules.task_executor import TaskExecutor
from agent.aether_orchestrator.modules.memory_handler import MemoryHandler
from agent.aether_orchestrator.modules.telemetry_handler import TelemetryHandler
from agent.aether_orchestrator.modules.api_client import APIClient


class ActionContext(BaseModel):
    """Validated context for cognitive routing."""
    anomaly: float = 0.0
    novelty: float = 0.1
    goal_alignment: float = 1.0

    class Config:
        extra = "allow"


class SynapticMessage(BaseModel):
    """Top-level schema for incoming JSON synaptic signals."""
    data: ActionContext = Field(default_factory=ActionContext)


class AetherCoreOrchestrator:
    """
    The main asynchronous event loop for AetherOS.
    Bridges the Edge Client (Sensory) via WebSockets to the DNA Brain.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8000, drift_threshold_ms: float = 500.0):
        self.host = host
        self.port = port
        self.drift_threshold_ms = drift_threshold_ms

        # Initialize core components
        self.bridge = AetherNavigator()
        self.router = HyperMindRouter(self.bridge)
        self.forge = AetherForge()
        self.memory_signal = MemorySignal()
        self.api_key = os.getenv("GEMINI_API_KEY")

        # Initialize modular components
        self.agent_manager = AgentManager(self.bridge, self.forge, drift_threshold_ms)
        self.memory_handler = MemoryHandler(self.memory_signal)
        self.telemetry_handler = TelemetryHandler(monitor)
        self.api_client = APIClient(self.bridge, self.api_key)

        # Task executor requires router and forge
        self.task_executor = TaskExecutor(
            self.bridge,
            self.router,
            self.forge,
            self.memory_signal,
            drift_threshold_ms
        )

    async def boot_sequence(self):
        """
        Initializes DNA and validates Persona logic.

        Delegates to AgentManager for boot sequence.
        """
        await self.agent_manager.boot_sequence()

    async def pulse_monitor(self, interval: float = 1.0):
        """
        Cognitive Pacemaker: Detects deadlocks and zombie connections.

        Delegates to AgentManager for pulse monitoring.
        """
        await self.agent_manager.pulse_monitor(interval)

    def _update_memory(self, result: ForgeResult):
        """
        Updates short-term memory signal with forge result.

        Delegates to MemoryHandler for memory updates.
        """
        self.memory_handler.update_memory(result)

    async def handle_optic_nerve(self, websocket):
        """
        Processes real-time binary/JSON synaptic bridge signals.

        Delegates to TaskExecutor for websocket handling.
        """
        # Create Gemini Live client
        gemini = self.api_client.create_gemini_client()
        # Handle connection in background to avoid blocking the bridge
        await self.api_client.connect_gemini_client(gemini)

        # Define callbacks for task executor
        def log_anomaly(component: str, error_type: str, message: str):
            self.telemetry_handler.log_anomaly(component, error_type, message)

        def trigger_healing(error_context: Dict[str, str], file_path: str):
            return evolve_engine.trigger_healing(error_context, file_path)

        # Handle websocket messages
        await self.task_executor.handle_optic_nerve(
            websocket,
            gemini,
            self._update_memory,
            log_anomaly,
            trigger_healing
        )

    async def shutdown(self):
        """
        Graceful shutdown with resource cleanup.

        Delegates to AgentManager for shutdown.
        """
        await self.agent_manager.shutdown()

    async def run_server(self):
        """Run the websocket server."""
        await self.boot_sequence()
        print(f"🛰️ Synaptic Bridge Listening on ws://{self.host}:{self.port}...")
        async with websockets.serve(self.handle_optic_nerve, self.host, self.port):
            await asyncio.Future()  # Run forever


if __name__ == "__main__":
    orchestrator = AetherCoreOrchestrator()
    asyncio.run(orchestrator.run_server())
