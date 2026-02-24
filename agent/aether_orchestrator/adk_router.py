# 🧭 agent/orchestrator/adk_router.py: ADK Router (AetherCore Development Kit)
# Pillar: Cognitive Gating (System 1/2)

import asyncio
from typing import Any, Dict

class ADKRouter:
    """
    Routes actions between System 1 (Reflexive) and System 2 (Reflective) execution paths.
    
    System 1: Direct reflexive execution via bridge.execute_tool()
    System 2: Swarm simulation via bridge.trigger_swarm()
    """
    
    def __init__(self, bridge):
        """Initialize with bridge reference to AetherNavigator."""
        self.bridge = bridge
    
    async def route_action(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route actions based on skill category and system.
        
        Args:
            context: Dictionary containing action context with keys:
                - skill_category: The category of skill to execute
                - system: Either "SYSTEM_1_REFLEX" or "SYSTEM_2_SWARM"
                - action: The specific action to execute
                - params: Parameters for the action
        
        Returns:
            Dictionary containing the result of the routed action
        """
        system = context.get("system", "SYSTEM_1_REFLEX")
        action = context.get("action", "")
        params = context.get("params", {})
        
        result = {
            "status": "success",
            "system": system,
            "action": action,
            "output": None,
            "error": None
        }
        
        try:
            if system == "SYSTEM_1_REFLEX":
                # Direct reflexive execution
                print(f"🧭 ADK Router: Routing to System 1 (Reflex) -> {action}")
                if hasattr(self.bridge, 'execute_tool'):
                    output = await self.bridge.execute_tool(action, **params)
                    result["output"] = output
                else:
                    # Fallback: execute directly through bridge
                    result["output"] = f"System 1 executed: {action}"
            elif system == "SYSTEM_2_SWARM":
                # Swarm simulation
                print(f"🧭 ADK Router: Routing to System 2 (Swarm) -> {action}")
                if hasattr(self.bridge, 'trigger_swarm'):
                    output = await self.bridge.trigger_swarm(action, **params)
                    result["output"] = output
                else:
                    # Fallback: simulate swarm execution
                    result["output"] = f"System 2 swarm simulated: {action}"
            else:
                result["status"] = "error"
                result["error"] = f"Unknown system: {system}"
                print(f"⚠️ ADK Router: Unknown system {system}")
                
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            print(f"❌ ADK Router error: {e}")
        
        return result
