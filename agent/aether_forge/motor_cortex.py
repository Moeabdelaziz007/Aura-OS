"""
⚙️ AetherOS — Motor Cortex (Tool Dispatcher)
===========================================
High-speed bridge between Gemini Live ToolCalls and local AetherForge execution.
Includes the Generative Micro-UI tool for materializing UI from voice commands.

API Ref: https://ai.google.dev/gemini-api/docs/function-calling
"""

import logging
import json
import uuid
import time
from typing import Any, Callable, Dict, List, Optional

from .aether_forge import AetherForge

logger = logging.getLogger("aether.motor")


class AetherMotorCortex:
    """
    The Omni-Action Execution Engine.

    Bridges Gemini Live tool calls to local execution:
    - execute_api_request → AetherForge (NanoAgent Swarm)
    - generate_ui → Micro-UI manifest (WebSocket → Edge Client)
    - manipulate_dom → Screen interaction (simulated)
    """

    def __init__(self, forge: Optional[AetherForge] = None):
        self.forge = forge or AetherForge()
        self._ui_callback: Optional[Callable] = None

        # Tool registry — maps Gemini function names to handlers
        self.tools: Dict[str, Callable] = {
            "execute_api_request": self._execute_api_request,
            "generate_ui": self._generate_ui,
            "manipulate_dom": self._manipulate_dom,
        }

    def set_ui_callback(self, callback: Callable):
        """Register a callback for pushing UI manifests to the Edge Client."""
        self._ui_callback = callback

    async def dispatch(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatch a Gemini tool call to the appropriate handler.

        Args:
            name: Tool function name from Gemini.
            args: Arguments dict from the function call.

        Returns:
            Result dict to send back to Gemini as function response.
        """
        logger.info(f"🦾 Motor Cortex: Dispatching '{name}'")

        handler = self.tools.get(name)
        if not handler:
            logger.warning(f"⚠️ Unknown tool: '{name}'. Available: {list(self.tools.keys())}")
            return {"error": f"Tool '{name}' is unknown to the Motor Cortex."}

        try:
            result = await handler(args)
            logger.info(f"✅ Motor Cortex: '{name}' completed successfully.")
            return result
        except Exception as e:
            logger.error(f"❌ Motor Cortex Execution Fault on '{name}': {e}", exc_info=True)
            return {"error": str(e)}

    # ─────────────────────────────────────────────
    # Tool 1: execute_api_request → AetherForge
    # ─────────────────────────────────────────────

    async def _execute_api_request(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Bridges Gemini to AetherForge for data retrieval.

        Supported services: coingecko, github, weather
        Flow: Tool call → AetherForge → NanoAgent Swarm → Consensus → Result
        """
        service = args.get("service")
        params = args.get("params", {})

        # Handle params as string (Gemini sometimes sends stringified JSON)
        if isinstance(params, str):
            try:
                params = json.loads(params)
            except json.JSONDecodeError:
                pass

        if not service:
            return {"error": "Missing 'service' parameter. Use: coingecko, github, weather"}

        intent_data = {"service": service, "params": params}
        result = await self.forge.aether_forge_and_deploy(intent_data)

        return {
            "success": result.success,
            "service": result.service,
            "data": result.data,
            "error": result.error if not result.success else None,
        }

    # ─────────────────────────────────────────────
    # Tool 2: generate_ui → Micro-UI Manifest
    # ─────────────────────────────────────────────

    async def _generate_ui(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a Micro-UI manifest for the Edge Client.

        Gemini calls this when the user asks to see something visual.
        The manifest is a JSON description of what to render:
        - component: Registry key (TaskListCard, CryptoCard, etc.)
        - props: Data to pass to the component
        - animation: How it appears (materialize, slide, fade)

        The manifest is pushed via WebSocket to the Edge Client,
        which renders the React component with Framer Motion animations.
        """
        component_type = args.get("type", "InfoCard")
        title = args.get("title", "")
        data = args.get("data", {})
        layout = args.get("layout", "card")

        # Map high-level types to component registry keys
        component_map = {
            "task_list": "TaskListCard",
            "crypto": "CryptoCard",
            "weather": "WeatherCard",
            "news": "NewsCard",
            "calendar": "CalendarView",
            "code": "CodeBlock",
            "chart": "ChartCard",
            "table": "DataTable",
            "info": "InfoCard",
        }

        component = component_map.get(component_type, "InfoCard")

        # Build the UI manifest
        manifest = {
            "action": "RENDER_UI",
            "component": component,
            "props": {
                "title": title,
                "data": data,
                "layout": layout,
            },
            "animation": "materialize",  # Particle burst → glassmorphism solidify
            "id": f"ui-{uuid.uuid4().hex[:8]}",
            "timestamp": time.time(),
            "ttl_seconds": 600,  # Auto-dissolves in 10 minutes
        }

        # Push to Edge Client if callback is registered
        if self._ui_callback:
            try:
                await self._ui_callback(manifest)
                logger.info(f"✨ Micro-UI pushed: {component} (id: {manifest['id']})")
            except Exception as e:
                logger.error(f"❌ UI push failed: {e}")

        return {
            "success": True,
            "message": f"UI component '{component}' materialized on screen.",
            "component": component,
            "ui_id": manifest["id"],
        }

    # ─────────────────────────────────────────────
    # Tool 3: manipulate_dom → Screen Interaction
    # ─────────────────────────────────────────────

    async def _manipulate_dom(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulates UI interaction based on visual context.
        Used when Gemini sees a screen and wants to interact with elements.
        """
        element_id = args.get("element_id", "unknown")
        action = args.get("action", "click")

        logger.info(f"🖱️ DOM Manipulation: {action} on '{element_id}'")
        return {
            "success": True,
            "message": f"Executed '{action}' on element '{element_id}'.",
        }


# ─────────────────────────────────────────────
# Tool Declarations (Gemini Function Calling Schema)
# ─────────────────────────────────────────────

def get_tool_declarations() -> List[Dict]:
    """
    Returns OpenAPI-compliant function declarations for Gemini Live API.
    These tell Gemini what tools are available and how to call them.

    Ref: https://ai.google.dev/gemini-api/docs/function-calling
    """
    return [{
        "function_declarations": [
            {
                "name": "execute_api_request",
                "description": (
                    "Executes a data retrieval request through AetherForge. "
                    "Use for: crypto prices (coingecko), weather data (weather), "
                    "GitHub repository info (github). Returns structured data."
                ),
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "service": {
                            "type": "STRING",
                            "description": "Service name: 'coingecko', 'github', or 'weather'"
                        },
                        "params": {
                            "type": "OBJECT",
                            "description": "Parameters for the service (e.g., {'coins': ['bitcoin']})"
                        }
                    },
                    "required": ["service"]
                }
            },
            {
                "name": "generate_ui",
                "description": (
                    "Materializes a visual UI component on the user's screen. "
                    "Use when the user asks to SEE something (charts, cards, lists, dashboards). "
                    "The UI appears from nothing with a particle animation effect. "
                    "Types: task_list, crypto, weather, news, calendar, code, chart, table, info."
                ),
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "type": {
                            "type": "STRING",
                            "description": "UI type: 'task_list', 'crypto', 'weather', 'news', 'calendar', 'code', 'chart', 'table', 'info'"
                        },
                        "title": {
                            "type": "STRING",
                            "description": "Title displayed on the UI card"
                        },
                        "data": {
                            "type": "OBJECT",
                            "description": "Data to display in the component (varies by type)"
                        },
                        "layout": {
                            "type": "STRING",
                            "description": "Layout mode: 'card' (default), 'fullscreen', 'sidebar'"
                        }
                    },
                    "required": ["type", "title"]
                }
            },
            {
                "name": "manipulate_dom",
                "description": (
                    "Interacts with a UI element visible on the user's screen. "
                    "Use when the user asks to click, scroll, or interact with something they see."
                ),
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "element_id": {
                            "type": "STRING",
                            "description": "The logical ID or description of the UI element"
                        },
                        "action": {
                            "type": "STRING",
                            "description": "Action: 'click', 'scroll', 'input', 'hover'"
                        }
                    },
                    "required": ["element_id", "action"]
                }
            }
        ]
    }]
