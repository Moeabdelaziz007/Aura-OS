"""
API Client Module

Handles API client operations and integrations for the AetherOS orchestrator.

Classes:
    APIClient: Manages external API client connections and operations
"""

import asyncio
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from agent.aether_orchestrator.memory_parser import AetherNavigator
    from agent.aether_orchestrator.gemini_live_client import GeminiLiveClient


class APIClient:
    """
    Manages API client connections and operations.

    Responsible for:
    - Gemini Live client initialization and lifecycle
    - Managing client connections
    - Handling client connection errors
    """

    def __init__(self, bridge: "AetherNavigator", api_key: str):
        """
        Initialize the API Client Manager.

        Args:
            bridge: The AetherNavigator for memory operations
            api_key: The API key for Gemini Live
        """
        self.bridge = bridge
        self.api_key = api_key
        self._gemini_client: Optional["GeminiLiveClient"] = None

    def create_gemini_client(self) -> "GeminiLiveClient":
        """
        Create and initialize a new Gemini Live client.

        Returns:
            A new GeminiLiveClient instance
        """
        from agent.aether_orchestrator.gemini_live_client import GeminiLiveClient

        self._gemini_client = GeminiLiveClient(self.bridge, self.api_key)
        return self._gemini_client

    async def connect_gemini_client(self, client: "GeminiLiveClient") -> None:
        """
        Connect the Gemini Live client in the background.

        Args:
            client: The GeminiLiveClient to connect
        """
        asyncio.create_task(client.connect())

    async def close_gemini_client(self, client: "GeminiLiveClient") -> None:
        """
        Close the Gemini Live client connection.

        Args:
            client: The GeminiLiveClient to close
        """
        await client.close()

    def get_current_client(self) -> Optional["GeminiLiveClient"]:
        """
        Get the current Gemini Live client instance.

        Returns:
            The current GeminiLiveClient or None if not initialized
        """
        return self._gemini_client

    def set_api_key(self, api_key: str) -> None:
        """
        Update the API key for future client connections.

        Args:
            api_key: The new API key to use
        """
        self.api_key = api_key

    def get_api_key(self) -> str:
        """
        Get the current API key.

        Returns:
            The current API key
        """
        return self.api_key
