"""
💻 Aether Terminal Sovereign
============================
Local Shell Execution Engine.
Pattern: Command + Proxy (with constraints).
"""

import asyncio
import logging
import shlex
from typing import Any, Dict
from ..registry import AetherSuperpower

logger = logging.getLogger("🧬 TerminalExecutor")

class AetherTerminalExecutor(AetherSuperpower):
    """
    Executes local shell commands.
    WARNING: Highly sensitive. Requires 'auth_required' in manifest (logic handled in Forge).
    """

    async def execute(self, args: Dict[str, Any]) -> Any:
        command = args.get("command")
        if not command:
            return {"error": "Missing 'command' parameter."}

        # BLOCKLIST for safety (MVP protection)
        forbidden = ["rm -rf /", "mkfs", "dd ", "> /dev/"]
        if any(f in command for f in forbidden):
            return {"error": "Security Breach Attempt: Command blocked by AetherCore Protocol."}

        logger.info(f"🐚 Executing: {command}")
        
        try:
            cmd_args = shlex.split(command)
            process = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            return {
                "command": command,
                "exit_code": process.returncode,
                "stdout": stdout.decode().strip(),
                "stderr": stderr.decode().strip(),
                "status": "success" if process.returncode == 0 else "failed"
            }
        except Exception as e:
            logger.error(f"❌ Terminal execution failed: {e}")
            return {"error": f"Terminal fault: {str(e)}"}
