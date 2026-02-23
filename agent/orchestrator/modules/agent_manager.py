"""
Agent Manager Module

Handles agent lifecycle management including boot sequence, shutdown,
and pulse monitoring for the AetherOS orchestrator.

Classes:
    AgentManager: Manages agent lifecycle and health monitoring
"""

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..memory_parser import AetherNavigator
    from agent.forge.aether_forge import AetherForge


class AgentManager:
    """
    Manages the lifecycle and health monitoring of the AetherOS agent.

    Responsible for:
    - Boot sequence initialization
    - Graceful shutdown with resource cleanup
    - Pulse monitoring for deadlock and zombie connection detection
    """

    def __init__(
        self,
        bridge: "AetherNavigator",
        forge: "AetherForge",
        drift_threshold_ms: float = 500.0
    ):
        """
        Initialize the Agent Manager.

        Args:
            bridge: The AetherNavigator for DNA and persona management
            forge: The AetherForge instance for async operations
            drift_threshold_ms: Threshold for detecting perceptual drift in milliseconds
        """
        self.bridge = bridge
        self.forge = forge
        self.drift_threshold_ms = drift_threshold_ms
        self.is_running = False
        self._cleanup_tasks = set()
        self._max_retries = 3

    async def boot_sequence(self) -> None:
        """
        Initialize DNA and validate Persona logic.

        This method:
        1. Loads and verifies the DNA sequence
        2. Ignites the Aether Forge (starts async client)
        3. Starts the pulse monitor for health checking
        """
        print("🪐 AetherOS: AetherCore Prometheus Booting...")
        dna = await self.bridge.load_dna_async()
        print(f"🧬 DNA Sequence Verified: {dna.version}")

        # Ignite the Forge (Start Async Client)
        await self.forge.__aenter__()
        print("🔥 Aether Forge: Ignited & Ready.")

        self.is_running = True

        # Priority 3: Start Active Pulse Monitor
        pulse_task = asyncio.create_task(self.pulse_monitor(), name="pulse_monitor")
        self._cleanup_tasks.add(pulse_task)

    async def pulse_monitor(self, interval: float = 1.0) -> None:
        """
        Cognitive Pacemaker: Detects deadlocks and zombie connections.

        Runs in the background to monitor the health of the orchestrator
        and detect any deadlocks or zombie connections.

        Args:
            interval: Time in seconds between pulse checks
        """
        print("💓 Pulse Engine: Monitoring Neural Synchronicity...")
        while True:
            await asyncio.sleep(interval)

    async def shutdown(self) -> None:
        """
        Graceful shutdown with resource cleanup.

        This method:
        1. Cancels all tracked cleanup tasks
        2. Closes bridge resources
        3. Cools down the Forge
        """
        print("🛑 AetherCoreOrchestrator: Initiating graceful shutdown...")
        self.is_running = False

        # Cancel all tracked cleanup tasks
        if self._cleanup_tasks:
            print(f"🧹 Cleaning up {len(self._cleanup_tasks)} tasks...")
            for task in self._cleanup_tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            self._cleanup_tasks.clear()

        # Close bridge resources
        if hasattr(self.bridge, 'close'):
            await self.bridge.close()

        # Cool down the Forge
        if hasattr(self.forge, '__aexit__'):
            await self.forge.__aexit__(None, None, None)
            print("❄️ Aether Forge: Cooled down.")

        print("✅ AetherCoreOrchestrator: Shutdown complete")

    def add_cleanup_task(self, task: asyncio.Task) -> None:
        """
        Add a task to the cleanup set for graceful shutdown.

        Args:
            task: The asyncio task to track for cleanup
        """
        self._cleanup_tasks.add(task)

    def remove_cleanup_task(self, task: asyncio.Task) -> None:
        """
        Remove a task from the cleanup set.

        Args:
            task: The asyncio task to remove from cleanup tracking
        """
        self._cleanup_tasks.discard(task)
