"""
Memory Handler Module

Handles memory operations and signal management for the AetherOS orchestrator.

Classes:
    MemoryHandler: Manages short-term memory signal updates and operations
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.aether_forge.constraint_solver import MemorySignal
    from agent.aether_forge.models import ForgeResult


class MemoryHandler:
    """
    Manages memory operations and signal updates.

    Responsible for:
    - Updating short-term memory signal with forge results
    - Tracking recent services and assets
    - Maintaining query statistics
    """

    def __init__(self, memory_signal: "MemorySignal"):
        """
        Initialize the Memory Handler.

        Args:
            memory_signal: The MemorySignal for short-term session memory
        """
        self.memory_signal = memory_signal

    def update_memory(self, result: "ForgeResult") -> None:
        """
        Update short-term memory signal with forge result.

        This method:
        1. Updates the recent services list (max 5 entries)
        2. Extracts and updates the recent assets list (max 5 entries)
        3. Updates the last action
        4. Increments the query count

        Args:
            result: The ForgeResult containing service and data information
        """
        # 1. Update Services
        self.memory_signal.recent_services.append(result.service)
        if len(self.memory_signal.recent_services) > 5:
            self.memory_signal.recent_services.pop(0)

        # 2. Extract Asset/Entity
        asset = "unknown"
        data = result.data or {}

        # Heuristics for asset extraction based on service
        if result.service == "coingecko":
            # Data: {'BTC': {...}, 'trend_data': ...}. Keys are usually assets.
            keys = [k for k in data.keys() if k != "trend_data"]
            if keys:
                asset = keys[0]
        elif result.service == "github":
            asset = data.get("Query", "unknown")
        elif result.service == "weather":
            asset = data.get("City", "unknown")

        self.memory_signal.recent_assets.append(asset)
        if len(self.memory_signal.recent_assets) > 5:
            self.memory_signal.recent_assets.pop(0)

        self.memory_signal.last_action = result.service
        self.memory_signal.query_count_1h += 1

    def get_recent_services(self) -> list:
        """
        Get the list of recent services.

        Returns:
            List of recent service names
        """
        return list(self.memory_signal.recent_services)

    def get_recent_assets(self) -> list:
        """
        Get the list of recent assets.

        Returns:
            List of recent asset names
        """
        return list(self.memory_signal.recent_assets)

    def get_last_action(self) -> str:
        """
        Get the last action performed.

        Returns:
            The name of the last service/action
        """
        return self.memory_signal.last_action

    def get_query_count(self) -> int:
        """
        Get the query count for the current hour.

        Returns:
            Number of queries in the last hour
        """
        return self.memory_signal.query_count_1h

    def reset_query_count(self) -> None:
        """Reset the query count (typically called hourly)."""
        self.memory_signal.query_count_1h = 0
