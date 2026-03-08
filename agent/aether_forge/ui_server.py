"""
🌐 AetherOS — UI WebSocket Server
===================================
Lightweight async WebSocket server that pushes Micro-UI manifests
from the Motor Cortex to the Edge Client in real-time.

Protocol:
    Server → Client:
        RENDER_UI   — Materialize a new component
        UPDATE_UI   — Update props of existing component
        DISSOLVE_UI — Remove component with dissolve animation
        CLEAR_ALL   — Remove all components

    Client → Server:
        UI_EVENT    — User interaction with a component (click, etc.)
        HEARTBEAT   — Connection keepalive

Architecture:
    Motor Cortex → micro_ui.generate() → ui_server.broadcast()
    → WebSocket → Edge Client React app
"""

import asyncio
import json
import logging
import time
from typing import Any, Callable, Dict, Optional, Set

import websockets
from websockets.asyncio.server import serve, ServerConnection

from .micro_ui import AetherMicroUIGenerator, UIManifest

logger = logging.getLogger("aether.ui_server")


# ─────────────────────────────────────────────
# Server Configuration
# ─────────────────────────────────────────────

DEFAULT_HOST = "0.0.0.0"  # Listen on all interfaces
DEFAULT_PORT = 8765        # WebSocket port
HEARTBEAT_INTERVAL = 30    # Seconds between keepalive pings
TTL_CHECK_INTERVAL = 60    # Seconds between TTL expiry checks


class AetherUIServer:
    """
    WebSocket server for real-time UI manifest delivery.

    Manages connected Edge Clients and broadcasts UI events.
    Integrates with AetherMicroUIGenerator for manifest generation.
    """

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        generator: Optional[AetherMicroUIGenerator] = None,
    ):
        self.host = host
        self.port = port
        self.generator = generator or AetherMicroUIGenerator()
        self._clients: Set[ServerConnection] = set()
        self._running = False
        self._event_handlers: Dict[str, Callable] = {}

        logger.info(f"🌐 UI Server configured on ws://{host}:{port}")

    @property
    def client_count(self) -> int:
        return len(self._clients)

    def on_event(self, event_type: str, handler: Callable):
        """Register a handler for client-side UI events."""
        self._event_handlers[event_type] = handler

    # ─────────────────────────────────────────────
    # Client Management
    # ─────────────────────────────────────────────

    async def _register(self, ws: ServerConnection):
        """Register a new Edge Client connection."""
        self._clients.add(ws)
        logger.info(f"✅ Edge Client connected. Total: {self.client_count}")

        # Send current UI state to new client (sync active components)
        for manifest in self.generator.state._active.values():
            try:
                await ws.send(json.dumps(manifest.to_dict()))
            except Exception:
                pass

    async def _unregister(self, ws: ServerConnection):
        """Remove a disconnected Edge Client."""
        self._clients.discard(ws)
        logger.info(f"📤 Edge Client disconnected. Total: {self.client_count}")

    # ─────────────────────────────────────────────
    # Broadcasting
    # ─────────────────────────────────────────────

    async def broadcast(self, message: Dict[str, Any]):
        """
        Send a message to ALL connected Edge Clients.
        Used for RENDER_UI, DISSOLVE_UI, CLEAR_ALL events.
        """
        if not self._clients:
            logger.debug("No clients connected. Message queued in state only.")
            return

        payload = json.dumps(message)
        clients_list = list(self._clients)

        # Broadcast concurrently using asyncio.gather
        tasks = [ws.send(payload) for ws in clients_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        dead_clients = set()
        for ws, result in zip(clients_list, results):
            if isinstance(result, websockets.exceptions.ConnectionClosed):
                dead_clients.add(ws)
            elif isinstance(result, Exception):
                logger.error(f"❌ Broadcast error: {result}")
                dead_clients.add(ws)

        # Clean up dead connections
        for ws in dead_clients:
            self._clients.discard(ws)

    async def push_ui(
        self,
        component_type: str,
        title: str = "",
        data: Optional[Dict] = None,
        **kwargs,
    ) -> UIManifest:
        """
        Generate a UI manifest and broadcast it to all clients.

        This is the main entry point for the Motor Cortex:
            motor_cortex._generate_ui() → ui_server.push_ui()

        Args:
            component_type: Component type (crypto, task_list, weather, etc.)
            title: Display title
            data: Raw data for the component

        Returns:
            The generated UIManifest
        """
        manifest = self.generator.generate(
            component_type=component_type,
            title=title,
            data=data,
            **kwargs,
        )
        await self.broadcast(manifest.to_dict())
        return manifest

    async def dissolve_ui(self, ui_id: str):
        """Dissolve a specific component on all clients."""
        cmd = self.generator.dissolve(ui_id)
        if cmd:
            await self.broadcast(cmd)

    async def clear_all(self):
        """Clear all UI components on all clients."""
        cmds = self.generator.clear_screen()
        for cmd in cmds:
            await self.broadcast(cmd)

    # ─────────────────────────────────────────────
    # Connection Handler
    # ─────────────────────────────────────────────

    async def _handler(self, ws: ServerConnection):
        """Handle a single WebSocket connection lifecycle."""
        await self._register(ws)
        try:
            async for message in ws:
                await self._handle_client_message(ws, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self._unregister(ws)

    async def _handle_client_message(self, ws: ServerConnection, raw: str):
        """
        Process incoming messages from Edge Client.
        Handles: UI_EVENT, HEARTBEAT
        """
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning(f"⚠️ Invalid JSON from client: {raw[:100]}")
            return

        action = msg.get("action", "")

        if action == "HEARTBEAT":
            await ws.send(json.dumps({"action": "HEARTBEAT_ACK", "t": time.time()}))

        elif action == "UI_EVENT":
            event_type = msg.get("event", "")
            handler = self._event_handlers.get(event_type)
            if handler:
                try:
                    await handler(msg)
                except Exception as e:
                    logger.error(f"❌ Event handler error: {e}")
            else:
                logger.debug(f"Unhandled UI event: {event_type}")

        else:
            logger.debug(f"Unknown client action: {action}")

    # ─────────────────────────────────────────────
    # TTL Auto-Dissolution Loop
    # ─────────────────────────────────────────────

    async def _ttl_check_loop(self):
        """Periodically check for expired UI components and dissolve them."""
        while self._running:
            await asyncio.sleep(TTL_CHECK_INTERVAL)
            expired_cmds = self.generator.dissolve_expired()
            for cmd in expired_cmds:
                await self.broadcast(cmd)

    # ─────────────────────────────────────────────
    # Server Lifecycle
    # ─────────────────────────────────────────────

    async def start(self):
        """Start the WebSocket server."""
        self._running = True
        logger.info(f"🚀 AetherOS UI Server starting on ws://{self.host}:{self.port}")

        async with serve(self._handler, self.host, self.port) as server:
            logger.info(f"✅ UI Server running. Waiting for Edge Clients...")

            # Run TTL checker in background
            ttl_task = asyncio.create_task(self._ttl_check_loop())

            try:
                await asyncio.Future()  # Run forever
            except asyncio.CancelledError:
                pass
            finally:
                ttl_task.cancel()
                self._running = False
                logger.info("🛑 UI Server stopped.")

    async def stop(self):
        """Stop the server gracefully."""
        self._running = False

    # ─────────────────────────────────────────────
    # Callback for Motor Cortex integration
    # ─────────────────────────────────────────────

    def get_ui_callback(self) -> Callable:
        """
        Returns an async callback for the Motor Cortex to push UI.

        Usage:
            bridge = AetherGeminiLiveBridgeV2()
            ui_server = AetherUIServer()
            bridge.set_ui_callback(ui_server.get_ui_callback())
        """
        async def _callback(manifest_or_result: Dict[str, Any]):
            # If it's already a manifest dict
            if "action" in manifest_or_result and manifest_or_result.get("action") == "RENDER_UI":
                await self.broadcast(manifest_or_result)
            # If it's a motor cortex result with component info
            elif "component" in manifest_or_result:
                await self.broadcast(manifest_or_result)
            else:
                logger.debug(f"UI callback received non-manifest data: {list(manifest_or_result.keys())}")

        return _callback


# ─────────────────────────────────────────────
# Self-test (non-blocking)
# ─────────────────────────────────────────────

async def _self_test():
    """Verify UI Server components work correctly."""
    server = AetherUIServer(port=8766)  # Use test port

    # Test 1: Generator integration
    manifest = await server.push_ui("crypto", "BTC Price", {
        "bitcoin": {"Price_USD": "$67,000", "Trend_24h": "▲ +1.5%"}
    })
    assert manifest.component == "CryptoCard"
    print(f"✅ Test 1: push_ui → CryptoCard (id={manifest.id})")

    # Test 2: State tracking
    assert server.generator.state.active_count == 1
    print(f"✅ Test 2: State tracks {server.generator.state.active_count} component")

    # Test 3: Dissolve
    await server.dissolve_ui(manifest.id)
    assert server.generator.state.active_count == 0
    print(f"✅ Test 3: Dissolved, {server.generator.state.active_count} remaining")

    # Test 4: Callback creation
    callback = server.get_ui_callback()
    assert callable(callback)
    print(f"✅ Test 4: UI callback created")

    # Test 5: Clear all
    await server.push_ui("weather", "Cairo", {"city": "Cairo", "temp_c": 30})
    await server.push_ui("news", "Headlines", {"articles": []})
    await server.clear_all()
    assert server.generator.state.active_count == 0
    print(f"✅ Test 5: Clear all works")

    print(f"\n🎉 All 5 UI Server tests passed!")


if __name__ == "__main__":
    asyncio.run(_self_test())
