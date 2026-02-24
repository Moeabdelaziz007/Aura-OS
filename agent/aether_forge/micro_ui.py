"""
✨ AetherOS — Generative Micro-UI Engine
=========================================
Generates UI component manifests from voice intent data.
These manifests are pushed via WebSocket to the Edge Client,
which renders React components with glassmorphism + particle animations.

The key insight: UI doesn't pre-exist. It materializes from the void
when the user speaks — then dissolves when no longer needed.

Architecture:
    Gemini Live → Motor Cortex → micro_ui.generate() → JSON Manifest
    → WebSocket → Edge Client → React Component + Framer Motion

Ref: Implementation Plan — Phase 2.1
"""

import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("aether.micro_ui")


# ─────────────────────────────────────────────
# Animation Types
# ─────────────────────────────────────────────

class AnimationType(str, Enum):
    """How a component appears/disappears on the Edge Client."""
    MATERIALIZE = "materialize"  # Particle burst → glassmorphism solidify
    SLIDE_UP = "slide_up"        # Slide from bottom with fade
    FADE = "fade"                # Simple opacity transition
    DISSOLVE = "dissolve"        # Reverse materialize — scatter to particles


class LayoutMode(str, Enum):
    """Where the component appears on screen."""
    CARD = "card"            # Floating card (default)
    FULLSCREEN = "fullscreen"  # Takes over entire viewport
    SIDEBAR = "sidebar"        # Slides in from right
    GRID = "grid"              # Part of a multi-component grid
    TOAST = "toast"            # Small notification-style popup


# ─────────────────────────────────────────────
# UI Manifest (The JSON that gets pushed to Edge Client)
# ─────────────────────────────────────────────

@dataclass
class UIManifest:
    """
    A complete description of a UI component to render.
    Serialized to JSON and sent via WebSocket to the Edge Client.
    """
    action: str = "RENDER_UI"
    component: str = "InfoCard"
    props: Dict[str, Any] = field(default_factory=dict)
    animation: str = AnimationType.MATERIALIZE.value
    layout: str = LayoutMode.CARD.value
    id: str = field(default_factory=lambda: f"ui-{uuid.uuid4().hex[:8]}")
    timestamp: float = field(default_factory=time.time)
    ttl_seconds: int = 600  # Auto-dissolve after 10 minutes
    priority: int = 0       # Higher = renders on top

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-safe dict for WebSocket transmission."""
        return asdict(self)

    def dissolve_manifest(self) -> Dict[str, Any]:
        """Generate the dissolve command for this component."""
        return {
            "action": "DISSOLVE_UI",
            "id": self.id,
            "animation": AnimationType.DISSOLVE.value,
        }


# ─────────────────────────────────────────────
# Component Factories (Voice Intent → UI Manifest)
# ─────────────────────────────────────────────

class ComponentFactory:
    """
    Creates UI manifests for specific component types.
    Each factory method transforms raw API data into a render-ready manifest.
    """

    @staticmethod
    def task_list(title: str, data: Dict[str, Any], **kwargs) -> UIManifest:
        """
        Task/ticket list view.
        Triggers: "show my tickets", "jira tasks", "todos"
        """
        # Extract items from data dict (flexible key lookup)
        items = data.get("items", data.get("tickets", data.get("tasks", [])))
        if not isinstance(items, list):
            items = []
        processed_items = []
        for item in items[:20]:  # Cap at 20 items
            processed_items.append({
                "id": item.get("id", ""),
                "title": item.get("title", item.get("name", "")),
                "status": item.get("status", "open"),
                "priority": item.get("priority", "normal"),
                "assignee": item.get("assignee", ""),
            })

        return UIManifest(
            component="TaskListCard",
            props={
                "title": title or "Tasks",
                "items": processed_items,
                "count": len(processed_items),
            },
            layout=LayoutMode.CARD.value if len(processed_items) <= 5 else LayoutMode.SIDEBAR.value,
            priority=2,
        )

    @staticmethod
    def crypto(title: str, data: Dict[str, Any], **kwargs) -> UIManifest:
        """
        Cryptocurrency price card with sparkline.
        Triggers: "bitcoin price", "show me crypto", "price of eth"
        """
        # Normalize data from CoinGecko executor
        coins = []
        for coin_id, coin_data in data.items():
            if coin_id in ("trend_data", "error"):
                continue
            if isinstance(coin_data, dict):
                coins.append({
                    "id": coin_id,
                    "name": coin_id.replace("-", " ").title(),
                    "price": coin_data.get("Price_USD", coin_data.get("price_usd", "$0")),
                    "change": coin_data.get("Trend_24h", coin_data.get("change_24h", "0%")),
                    "sparkline": coin_data.get("trend_data", []),
                })

        return UIManifest(
            component="CryptoCard",
            props={
                "title": title or "Crypto Prices",
                "coins": coins,
            },
            priority=1,
        )

    @staticmethod
    def weather(title: str, data: Dict[str, Any], **kwargs) -> UIManifest:
        """
        Weather information card.
        Triggers: "weather", "temperature", "is it going to rain"
        """
        return UIManifest(
            component="WeatherCard",
            props={
                "title": title or "Weather",
                "city": data.get("city", data.get("location", "Unknown")),
                "temp_c": data.get("temp_c", data.get("temperature", 0)),
                "condition": data.get("weather_code", data.get("condition", 0)),
                "wind_kmh": data.get("wind_kmh", data.get("wind", 0)),
                "humidity": data.get("humidity", 0),
            },
        )

    @staticmethod
    def news(title: str, data: Dict[str, Any], **kwargs) -> UIManifest:
        """
        News headlines card.
        Triggers: "news", "headlines", "what's happening"
        """
        articles = data.get("articles", data.get("items", []))
        processed = []
        for article in articles[:10]:
            processed.append({
                "title": article.get("title", ""),
                "source": article.get("source", ""),
                "url": article.get("url", ""),
                "time": article.get("published", article.get("time", "")),
            })

        return UIManifest(
            component="NewsCard",
            props={
                "title": title or "Headlines",
                "articles": processed,
            },
            layout=LayoutMode.SIDEBAR.value,
            priority=1,
        )

    @staticmethod
    def calendar(title: str, data: Dict[str, Any], **kwargs) -> UIManifest:
        """
        Calendar/schedule view.
        Triggers: "schedule", "meetings", "calendar", "what's next"
        """
        events = data.get("events", [])
        return UIManifest(
            component="CalendarView",
            props={
                "title": title or "Schedule",
                "events": events[:15],
                "date": data.get("date", "today"),
            },
            layout=LayoutMode.SIDEBAR.value,
        )

    @staticmethod
    def code(title: str, data: Dict[str, Any], **kwargs) -> UIManifest:
        """
        Code block display.
        Triggers: "show code", "patch", "diff", "snippet"
        """
        return UIManifest(
            component="CodeBlock",
            props={
                "title": title or "Code",
                "language": data.get("language", "python"),
                "code": data.get("code", data.get("content", "")),
                "filename": data.get("filename", ""),
            },
        )

    @staticmethod
    def chart(title: str, data: Dict[str, Any], **kwargs) -> UIManifest:
        """
        Data visualization chart.
        Triggers: "chart", "graph", "visualize", "compare"
        """
        return UIManifest(
            component="ChartCard",
            props={
                "title": title or "Chart",
                "type": data.get("chart_type", "line"),
                "labels": data.get("labels", []),
                "datasets": data.get("datasets", []),
            },
            layout=LayoutMode.CARD.value,
            priority=2,
        )

    @staticmethod
    def info(title: str, data: Dict[str, Any], **kwargs) -> UIManifest:
        """
        Generic information card (fallback).
        """
        return UIManifest(
            component="InfoCard",
            props={
                "title": title or "Info",
                "content": data,
            },
        )


# ─────────────────────────────────────────────
# Factory Registry
# ─────────────────────────────────────────────

COMPONENT_FACTORIES: Dict[str, Callable] = {
    "task_list": ComponentFactory.task_list,
    "crypto": ComponentFactory.crypto,
    "weather": ComponentFactory.weather,
    "news": ComponentFactory.news,
    "calendar": ComponentFactory.calendar,
    "code": ComponentFactory.code,
    "chart": ComponentFactory.chart,
    "table": ComponentFactory.info,  # Alias for now
    "info": ComponentFactory.info,
}


# ─────────────────────────────────────────────
# UI State Manager (Tracks active components)
# ─────────────────────────────────────────────

class UIStateManager:
    """
    Tracks currently active UI components on the Edge Client.
    Handles auto-dissolution when TTL expires.
    """

    def __init__(self):
        self._active: Dict[str, UIManifest] = {}

    @property
    def active_count(self) -> int:
        return len(self._active)

    @property
    def active_components(self) -> List[str]:
        return [m.component for m in self._active.values()]

    def register(self, manifest: UIManifest):
        """Track a newly rendered component."""
        self._active[manifest.id] = manifest
        logger.info(
            f"✨ UI registered: {manifest.component} (id={manifest.id}, "
            f"ttl={manifest.ttl_seconds}s, active={self.active_count})"
        )

    def unregister(self, ui_id: str) -> Optional[UIManifest]:
        """Remove a dissolved component from tracking."""
        manifest = self._active.pop(ui_id, None)
        if manifest:
            logger.info(f"💨 UI dissolved: {manifest.component} (id={ui_id})")
        return manifest

    def get_expired(self) -> List[UIManifest]:
        """Find components whose TTL has expired."""
        now = time.time()
        expired = []
        for manifest in self._active.values():
            age = now - manifest.timestamp
            if age > manifest.ttl_seconds:
                expired.append(manifest)
        return expired

    def clear_all(self) -> List[Dict]:
        """Generate dissolve commands for all active components."""
        dissolve_commands = []
        for manifest in self._active.values():
            dissolve_commands.append(manifest.dissolve_manifest())
        self._active.clear()
        logger.info("🧹 All UI components dissolved.")
        return dissolve_commands


# ─────────────────────────────────────────────
# Main Generator Class
# ─────────────────────────────────────────────

class AetherMicroUIGenerator:
    """
    The Generative Micro-UI Engine.

    Takes voice intent data and generates UI component manifests
    that materialize on the Edge Client.

    Usage:
        generator = AetherMicroUIGenerator()
        manifest = generator.generate("crypto", "Bitcoin Price", {"bitcoin": {...}})
        # → Send manifest.to_dict() via WebSocket to Edge Client
    """

    def __init__(self):
        self.state = UIStateManager()
        self._factories = COMPONENT_FACTORIES
        logger.info(
            f"✨ Micro-UI Generator initialized. "
            f"Components: {list(self._factories.keys())}"
        )

    def generate(
        self,
        component_type: str,
        title: str = "",
        data: Optional[Dict[str, Any]] = None,
        layout: Optional[str] = None,
        animation: Optional[str] = None,
    ) -> UIManifest:
        """
        Generate a UI manifest from intent data.

        Args:
            component_type: Type key (task_list, crypto, weather, news, etc.)
            title: Display title for the component
            data: Raw data to populate the component with
            layout: Override layout mode (card, fullscreen, sidebar, grid, toast)
            animation: Override animation type

        Returns:
            UIManifest ready for WebSocket transmission
        """
        factory = self._factories.get(component_type, ComponentFactory.info)
        manifest = factory(title=title, data=data or {})

        # Apply overrides
        if layout:
            manifest.layout = layout
        if animation:
            manifest.animation = animation

        # Track in state manager
        self.state.register(manifest)

        logger.info(
            f"🎨 Generated: {manifest.component} | "
            f"layout={manifest.layout} | animation={manifest.animation}"
        )
        return manifest

    def dissolve(self, ui_id: str) -> Optional[Dict]:
        """Generate a dissolve command for a specific component."""
        manifest = self.state.unregister(ui_id)
        if manifest:
            return manifest.dissolve_manifest()
        return None

    def dissolve_expired(self) -> List[Dict]:
        """Check for and dissolve expired components."""
        expired = self.state.get_expired()
        commands = []
        for manifest in expired:
            self.state.unregister(manifest.id)
            commands.append(manifest.dissolve_manifest())
        if commands:
            logger.info(f"⏰ Auto-dissolved {len(commands)} expired components.")
        return commands

    def clear_screen(self) -> List[Dict]:
        """Dissolve all active components (screen reset)."""
        return self.state.clear_all()


# ─────────────────────────────────────────────
# Self-test
# ─────────────────────────────────────────────

def _self_test():
    """Verify Micro-UI Generator works correctly."""
    import json

    generator = AetherMicroUIGenerator()

    # Test 1: Crypto card
    m1 = generator.generate("crypto", "Bitcoin Price", {
        "bitcoin": {"Price_USD": "$67,432.50", "Trend_24h": "▲ +2.3%"}
    })
    assert m1.component == "CryptoCard"
    assert m1.action == "RENDER_UI"
    assert "coins" in m1.props
    print(f"✅ Test 1 passed: {m1.component} (id={m1.id})")

    # Test 2: Task list
    m2 = generator.generate("task_list", "My Jira Tickets", {
        "items": [
            {"id": "PROJ-42", "title": "Fix auth bug", "priority": "P1", "status": "open"},
            {"id": "PROJ-43", "title": "Add dark mode", "priority": "P2", "status": "in_progress"},
        ]
    })
    assert m2.component == "TaskListCard"
    assert len(m2.props["items"]) == 2
    print(f"✅ Test 2 passed: {m2.component} ({m2.props['count']} items)")

    # Test 3: Weather
    m3 = generator.generate("weather", "Cairo Weather", {
        "city": "Cairo", "temp_c": 28.5, "wind_kmh": 15, "weather_code": 0
    })
    assert m3.component == "WeatherCard"
    assert m3.props["city"] == "Cairo"
    print(f"✅ Test 3 passed: {m3.component} ({m3.props['city']})")

    # Test 4: State tracking
    assert generator.state.active_count == 3
    print(f"✅ Test 4 passed: {generator.state.active_count} active components")

    # Test 5: Dissolve
    dissolve_cmd = generator.dissolve(m1.id)
    assert dissolve_cmd["action"] == "DISSOLVE_UI"
    assert generator.state.active_count == 2
    print(f"✅ Test 5 passed: Dissolved {m1.id}, {generator.state.active_count} remaining")

    # Test 6: Clear all
    clear_cmds = generator.clear_screen()
    assert len(clear_cmds) == 2
    assert generator.state.active_count == 0
    print(f"✅ Test 6 passed: Cleared all, {generator.state.active_count} remaining")

    # Test 7: Serialization
    m4 = generator.generate("news", "Headlines", {
        "articles": [{"title": "AI wins Nobel Prize", "source": "Reuters"}]
    })
    json_str = json.dumps(m4.to_dict(), indent=2)
    parsed = json.loads(json_str)
    assert parsed["component"] == "NewsCard"
    print(f"✅ Test 7 passed: JSON serialization ({len(json_str)} bytes)")
    print(f"\n📋 Sample manifest:\n{json_str}")

    # Test 8: Unknown type falls back to InfoCard
    m5 = generator.generate("unknown_type", "Fallback", {"key": "value"})
    assert m5.component == "InfoCard"
    print(f"✅ Test 8 passed: Unknown type → {m5.component}")

    print(f"\n🎉 All 8 tests passed! Micro-UI Generator is ready.")


if __name__ == "__main__":
    _self_test()
