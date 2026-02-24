"""
AetherOS - AetherTelemetry System
Manages real-time state persistence for the Pulse API.
Includes P95/P99 latency tracking and resource monitoring.
"""

import json
import os
import logging
import asyncio
import time
import psutil
from typing import Dict, Any, Optional
from collections import deque
from statistics import median
from datetime import datetime

TELEMETRY_FILE = "agent/aether_memory/TELEMETRY.json"
LATENCY_WINDOW_SIZE = 1000  # Keep last 1000 latency samples

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | 📊 AetherTelemetry | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("AetherTelemetryManager")


class AetherLatencyTracker:
    """
    Tracks latency measurements and calculates percentile metrics.
    Uses a rolling window of samples to maintain memory efficiency.
    """
    
    def __init__(self, window_size: int = LATENCY_WINDOW_SIZE):
        self.window_size = window_size
        self._latency_samples: deque[float] = deque(maxlen=window_size)
        self._resource_samples: deque[Dict[str, float]] = deque(maxlen=window_size)
    
    def aether_record_latency(self, latency_ms: float, resource_data: Optional[Dict[str, float]] = None) -> None:
        """
        Record a latency measurement with optional resource data.
        
        Args:
            latency_ms: Latency in milliseconds
            resource_data: Optional dict containing cpu_percent, memory_mb, energy_mJ
        """
        self._latency_samples.append(latency_ms)
        
        if resource_data:
            self._resource_samples.append(resource_data)
        else:
            # Capture default resource metrics if not provided
            self._resource_samples.append(self._aether_capture_current_resources())
    
    def _aether_capture_current_resources(self) -> Dict[str, float]:
        """
        Capture current system resource usage.
        
        Returns:
            Dict with cpu_percent, memory_mb, and energy_mJ (if available)
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=None)
            memory_info = psutil.virtual_memory()
            memory_mb = memory_info.used / (1024 * 1024)  # Convert to MB
            
            # Energy tracking - battery info if available
            energy_mj = 0.0
            try:
                if hasattr(psutil, 'sensors_battery'):
                    battery = psutil.sensors_battery()
                    if battery and hasattr(battery, 'power'):
                        # Power is in watts, convert to millijoules (assuming 1 second sampling)
                        energy_mj = battery.power * 1000 if battery.power else 0.0
            except Exception:
                pass  # Energy tracking not available
            
            return {
                "cpu_percent": cpu_percent,
                "memory_mb": memory_mb,
                "energy_mj": energy_mj
            }
        except Exception as e:
            logger.warning(f"Failed to capture resource metrics: {e}")
            return {"cpu_percent": 0.0, "memory_mb": 0.0, "energy_mj": 0.0}
    
    def aether_calculate_p50_latency(self) -> Optional[float]:
        """
        Calculate the median (P50) latency.
        
        Returns:
            Median latency in milliseconds, or None if no samples
        """
        if not self._latency_samples:
            return None
        return median(self._latency_samples)
    
    def aether_calculate_p95_latency(self) -> Optional[float]:
        """
        Calculate P95 latency (95th percentile).
        
        Returns:
            P95 latency in milliseconds, or None if no samples
        """
        if not self._latency_samples:
            return None
        
        sorted_samples = sorted(self._latency_samples)
        # Use ceiling for proper percentile calculation
        index = min(int(len(sorted_samples) * 0.95), len(sorted_samples) - 1)
        return sorted_samples[index]
    
    def aether_calculate_p99_latency(self) -> Optional[float]:
        """
        Calculate P99 latency (99th percentile).
        
        Returns:
            P99 latency in milliseconds, or None if no samples
        """
        if not self._latency_samples:
            return None
        
        sorted_samples = sorted(self._latency_samples)
        # Use ceiling for proper percentile calculation
        index = min(int(len(sorted_samples) * 0.99), len(sorted_samples) - 1)
        return sorted_samples[index]
    
    def aether_calculate_avg_latency(self) -> Optional[float]:
        """
        Calculate the average latency.
        
        Returns:
            Average latency in milliseconds, or None if no samples
        """
        if not self._latency_samples:
            return None
        return sum(self._latency_samples) / len(self._latency_samples)
    
    def aether_get_latency_samples(self) -> list:
        """
        Get all latency samples.
        
        Returns:
            List of latency samples
        """
        return list(self._latency_samples)
    
    def aether_get_resource_metrics(self) -> Dict[str, Any]:
        """
        Get aggregated resource metrics from all samples.
        
        Returns:
            Dict with avg_cpu_percent, avg_memory_mb, total_energy_mj
        """
        if not self._resource_samples:
            return {
                "avg_cpu_percent": 0.0,
                "avg_memory_mb": 0.0,
                "total_energy_mj": 0.0,
                "sample_count": 0
            }
        
        cpu_values = [s.get("cpu_percent", 0.0) for s in self._resource_samples]
        memory_values = [s.get("memory_mb", 0.0) for s in self._resource_samples]
        energy_values = [s.get("energy_mj", 0.0) for s in self._resource_samples]
        
        return {
            "avg_cpu_percent": sum(cpu_values) / len(cpu_values),
            "avg_memory_mb": sum(memory_values) / len(memory_values),
            "total_energy_mj": sum(energy_values),
            "sample_count": len(self._resource_samples)
        }
    
    def aether_get_percentile_metrics(self) -> Dict[str, Optional[float]]:
        """
        Get all percentile metrics.
        
        Returns:
            Dict with p50_latency_ms, p95_latency_ms, p99_latency_ms
        """
        return {
            "p50_latency_ms": self.aether_calculate_p50_latency(),
            "p95_latency_ms": self.aether_calculate_p95_latency(),
            "p99_latency_ms": self.aether_calculate_p99_latency()
        }
    
    def aether_clear(self) -> None:
        """Clear all latency and resource samples."""
        self._latency_samples.clear()
        self._resource_samples.clear()


class AetherTelemetryManager:
    # Class-level latency tracker instance
    _latency_tracker: Optional[AetherLatencyTracker] = None
    _latency_tracker_lock: asyncio.Lock = None  # Lock for thread-safe access
    
    @classmethod
    async def aether_get_latency_tracker(cls) -> AetherLatencyTracker:
        """
        Get or create shared latency tracker instance (thread-safe).
        
        Returns:
            AetherLatencyTracker instance
        """
        # Create lock if not exists (for backward compatibility with sync calls)
        if cls._latency_tracker_lock is None:
            cls._latency_tracker_lock = asyncio.Lock()
        
        async with cls._latency_tracker_lock:
            if cls._latency_tracker is None:
                cls._latency_tracker = AetherLatencyTracker()
            return cls._latency_tracker
    
    @staticmethod
    async def aether_record_request_latency(latency_ms: float, resource_data: Optional[Dict[str, float]] = None) -> None:
        """
        Record a request latency measurement (thread-safe).
        
        Args:
            latency_ms: Latency in milliseconds
            resource_data: Optional dict with cpu_percent, memory_mb, energy_mJ
        """
        tracker = await AetherTelemetryManager.aether_get_latency_tracker()
        tracker.aether_record_latency(latency_ms, resource_data)
        
        # Update telemetry file with latest metrics
        await AetherTelemetryManager._aether_update_latency_metrics()
    
    @staticmethod
    async def _aether_update_latency_metrics() -> None:
        """
        Update telemetry file with current latency and resource metrics.
        """
        tracker = await AetherTelemetryManager.aether_get_latency_tracker()
        
        latency_data = {
            "latency_sample_count": len(tracker.aether_get_latency_samples()),
            "p50_latency_ms": tracker.aether_calculate_p50_latency(),
            "p95_latency_ms": tracker.aether_calculate_p95_latency(),
            "p99_latency_ms": tracker.aether_calculate_p99_latency(),
            "avg_latency_ms": tracker.aether_calculate_avg_latency(),
            "resource_metrics": tracker.aether_get_resource_metrics(),
            "last_latency_update": datetime.utcnow().isoformat() + "Z"
        }
        
        await AetherTelemetryManager.aether_update(latency_data)
    
    @staticmethod
    async def aether_update(data: Dict[str, Any]):
        """
        Updates telemetry file with new data (merging top-level keys).
        
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
            # Continue anyway - file write will fail if directory doesn't exist
        except Exception as e:
            logger.error(f"❌ Unexpected error creating directory: {e}")

        # Read existing
        try:
            current = await AetherTelemetryManager.aether_read()
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
            # Don't re-raise - telemetry failures shouldn't break application

    @staticmethod
    async def aether_read() -> Dict[str, Any]:
        """
        Reads telemetry file and returns its contents.
        
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


# Convenience context manager for timing operations
class AetherLatencyTimer:
    """
    Context manager for timing operations and recording latency.
    
    Usage:
        async with AetherLatencyTimer() as timer:
            # do work
        # latency automatically recorded
    """
    
    def __init__(self, resource_data: Optional[Dict[str, float]] = None):
        self.resource_data = resource_data
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
    
    async def __aenter__(self):
        self.start_time = time.perf_counter()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        if self.start_time is not None and self.end_time is not None:
            latency_ms = (self.end_time - self.start_time) * 1000
            await AetherTelemetryManager.aether_record_request_latency(latency_ms, self.resource_data)
        return False
