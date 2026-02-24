"""
⚙️ AetherOS — Motor Cortex (Tool Dispatcher)
===========================================
High-speed bridge between Gemini ToolCalls and local AetherForge execution.
"""

import logging
import json
from typing import Any, Dict, Optional
from .aether_forge import AetherForge

logger = logging.getLogger("aether.motor")

class AetherMotorCortex:
    """The Omni-Action Execution Engine."""

    def __init__(self, forge: Optional[AetherForge] = None):
        self.forge = forge or AetherForge()
        self.tools = {
            "execute_api_request": self._execute_api_request,
            "manipulate_dom": self._manipulate_dom
        }

    async def dispatch(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch a tool call to the local implementation."""
        logger.info(f"🦾 MotorCortex: Dispatching {name} with args: {args}")
        
        handler = self.tools.get(name)
        if not handler:
            return {"error": f"Tool '{name}' is unknown to the Motor Cortex."}

        try:
            return await handler(args)
        except Exception as e:
            logger.error(f"❌ MotorCortex Execution Fault: {e}")
            return {"error": str(e)}

    async def aether_execute_api_request(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Bridges Gemini to AetherForge."""
        service = args.get("service")
        params = args.get("params", {})
        
        if isinstance(params, str):
            try:
                params = json.loads(params)
            except:
                pass

        if not service:
            return {"error": "Missing 'service' parameter."}

        # Intent Data for Forge
        intent_data = {
            "service": service,
            "params": params
        }

        result = await self.forge.aether_forge_and_deploy(intent_data)
        
        return {
            "success": result.success,
            "service": result.service,
            "data": result.data,
            "error": result.error if not result.success else None,
            "visual_feedback": result.ascii_visual
        }

    async def aether_manipulate_dom(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Simulator for UI interaction."""
        element_id = args.get("element_id")
        action = args.get("action")
        
        logger.info(f"🖱️ DOM Manipulation (MOCK): {action} on {element_id}")
        return {
            "success": True,
            "message": f"Successfully executed '{action}' on element '{element_id}' in the simulator."
        }

def get_tool_declarations() -> list:
    """Returns the OpenAPI-compliant declarations for Gemini Live API."""
    return [{
        "function_declarations": [
            {
                "name": "execute_api_request",
                "description": "Executes a high-level API request through the AetherForge engine. Use this for price checks, weather updates, or github searches.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "service": {
                            "type": "STRING",
                            "description": "The service name (e.g., 'coingecko', 'github', 'weather')"
                        },
                        "params": {
                            "type": "OBJECT",
                            "description": "JSON object containing API parameters (e.g., {'coins': ['bitcoin']})"
                        }
                    },
                    "required": ["service"]
                }
            },
            {
                "name": "manipulate_dom",
                "description": "Simulates UI interaction based on visual context. Use this for clicking buttons or filling forms seen on screen.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "element_id": {
                            "type": "STRING",
                            "description": "The logical ID or description of the UI element."
                        },
                        "action": {
                            "type": "STRING",
                            "description": "The action to perform (e.g., 'click', 'scroll', 'input')"
                        }
                    },
                    "required": ["element_id", "action"]
                }
            }
        ]
    }]
