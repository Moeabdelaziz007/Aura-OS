"""
Aether Forge - Nano-Agent Sandbox (Lightweight)
Executes generated Python code in a restricted namespace.
"""

import asyncio
import logging
import traceback
from typing import Any, Dict

# Whitelisted modules for dynamic agents
import httpx
import json
import re
import math
import datetime

logger = logging.getLogger("AetherSandbox")

class AetherExecutionResult:
    def __init__(self, success: bool, data: Any = None, error: str = None):
        self.success = success
        self.data = data
        self.error = error

class AetherNanoSandbox:
    def __init__(self):
        self.globals = {
            "__builtins__": {
                "print": print,
                "range": range,
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "dict": dict,
                "list": list,
                "set": set,
                "tuple": tuple,
                "Exception": Exception,
                "ValueError": ValueError,
                "KeyError": KeyError,
                "TypeError": TypeError,
                "max": max,
                "min": min,
                "sum": sum,
                "abs": abs,
                "round": round,
                "isinstance": isinstance,
                "enumerate": enumerate,
                "zip": zip,
            },
            "httpx": httpx,
            "json": json,
            "re": re,
            "math": math,
            "datetime": datetime,
            "asyncio": asyncio,
        }

        # Add safe import
        def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
            whitelist = {"httpx", "json", "re", "math", "datetime", "asyncio", "typing"}
            if name in whitelist:
                return __import__(name, globals, locals, fromlist, level)
            raise ImportError(f"Import of '{name}' is not allowed in sandbox.")

        self.globals["__builtins__"]["__import__"] = safe_import

    async def execute(self, code: str, params: Dict[str, Any]) -> AetherExecutionResult:
        """
        Executes the given Python code in a sandbox.
        Expects the code to define an async function `execute(params)`.
        """
        try:
            # Create a separate namespace for execution
            local_scope = {}

            # Exec the code definition (sync operation, fast)
            exec(code, self.globals, local_scope)

            # Check if 'execute' function exists
            if "execute" not in local_scope:
                return AetherExecutionResult(False, error="Code must define an 'execute(params)' function.")

            func = local_scope["execute"]

            if not callable(func):
                return AetherExecutionResult(False, error="'execute' is not callable.")

            # Run the agent function
            if asyncio.iscoroutinefunction(func):
                result = await func(params)
            else:
                # Allow sync functions too, run in thread to avoid blocking
                result = await asyncio.to_thread(func, params)

            return AetherExecutionResult(True, data=result)

        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Sandbox Execution Failed: {e}\n{tb}")
            return AetherExecutionResult(False, error=str(e))
