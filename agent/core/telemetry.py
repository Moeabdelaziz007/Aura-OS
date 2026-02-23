"""
AetherOS - Core Telemetry System
Manages real-time state persistence for the Pulse API.
"""

import json
import os
import logging
import asyncio
from typing import Dict, Any

TELEMETRY_FILE = "agent/memory/TELEMETRY.json"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | 📊 Telemetry | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("TelemetryManager")

class TelemetryManager:
    @staticmethod
    async def update(data: Dict[str, Any]):
        """
        Updates the telemetry file with new data (merging top-level keys).
        
        Args:
            data: Dictionary containing telemetry data to merge
        
        Raises:
            ValueError: If data is not a dictionary
        """
        # Validate input data
        if not isinstance(data, dict):
            logger.error(f"❌ Telemetry update failed: data must be a dictionary, got {type(data)}")
            raise ValueError("Telemetry data must be a dictionary")
        
        # Ensure directory exists
        try:
            telemetry_dir = os.path.dirname(TELEMETRY_FILE)
            if telemetry_dir:
                os.makedirs(telemetry_dir, exist_ok=True)
        except (PermissionError, OSError) as e:
            logger.error(f"❌ Failed to create telemetry directory: {e}")
            # Continue anyway - the file write will fail if directory doesn't exist
        except Exception as e:
            logger.error(f"❌ Unexpected error creating directory: {e}")

        # Read existing
        try:
            current = await TelemetryManager.read()
        except Exception as e:
            logger.warning(f"⚠️ Failed to read existing telemetry: {e}. Starting with empty data.")
            current = {}

        # Merge
        try:
            current.update(data)
        except Exception as e:
            logger.error(f"❌ Failed to merge telemetry data: {e}")
            raise

        # Write back via thread to avoid blocking loop
        def write_sync():
            temp_file = TELEMETRY_FILE + ".tmp"
            try:
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(current, f, indent=2)
                # Atomic replace operation
                os.replace(temp_file, TELEMETRY_FILE)
            except (PermissionError, OSError) as e:
                logger.error(f"❌ Telemetry write permission error: {e}")
                raise
            except (TypeError, ValueError) as e:
                logger.error(f"❌ Telemetry JSON serialization error: {e}")
                raise
            except Exception as e:
                logger.error(f"❌ Telemetry write error: {e}")
                raise

        try:
            await asyncio.to_thread(write_sync)
        except Exception as e:
            logger.error(f"❌ Telemetry write failed: {e}")
            # Don't re-raise - telemetry failures shouldn't break the application

    @staticmethod
    async def read() -> Dict[str, Any]:
        """
        Reads the telemetry file and returns its contents.
        
        Returns:
            Dictionary containing telemetry data, or empty dict if file doesn't exist or read fails
        """
        try:
            if not os.path.exists(TELEMETRY_FILE):
                logger.debug(f"Telemetry file not found at {TELEMETRY_FILE}, returning empty dict")
                return {}

            def read_sync():
                try:
                    with open(TELEMETRY_FILE, "r", encoding="utf-8") as f:
                        return json.load(f)
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Telemetry JSON decode error: {e}")
                    # Return empty dict on JSON parse error
                    return {}
                except (PermissionError, OSError) as e:
                    logger.error(f"❌ Telemetry read permission error: {e}")
                    raise
                except Exception as e:
                    logger.error(f"❌ Telemetry read error: {e}")
                    raise

            return await asyncio.to_thread(read_sync)
        except Exception as e:
            logger.warning(f"⚠️ Failed to read telemetry file: {e}. Returning empty dict.")
            return {}
