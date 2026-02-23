"""
AetherOS - Core Telemetry System
Manages real-time state persistence for the Pulse API.
"""

import json
import os
import asyncio
from typing import Dict, Any

TELEMETRY_FILE = "agent/memory/TELEMETRY.json"

class TelemetryManager:
    @staticmethod
    async def update(data: Dict[str, Any]):
        """Updates the telemetry file with new data (merging top-level keys)."""
        # Ensure directory exists
        try:
            os.makedirs(os.path.dirname(TELEMETRY_FILE), exist_ok=True)

            # Read existing
            current = await TelemetryManager.read()

            # Merge
            current.update(data)

            # Write back via thread to avoid blocking loop
            def write_sync():
                temp_file = TELEMETRY_FILE + ".tmp"
                with open(temp_file, "w") as f:
                    json.dump(current, f, indent=2)
                os.replace(temp_file, TELEMETRY_FILE)

            await asyncio.to_thread(write_sync)
        except Exception as e:
            print(f"⚠️ Telemetry Write Error: {e}")

    @staticmethod
    async def read() -> Dict[str, Any]:
        try:
            if not os.path.exists(TELEMETRY_FILE):
                return {}

            def read_sync():
                with open(TELEMETRY_FILE, "r") as f:
                    return json.load(f)

            return await asyncio.to_thread(read_sync)
        except Exception:
            return {}
