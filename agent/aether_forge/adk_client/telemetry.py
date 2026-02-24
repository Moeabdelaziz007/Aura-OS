"""
🧠 AetherOS ADK Client - Logging & Telemetry
============================================
Comprehensive logging and telemetry integration.
Supports multiple output sinks and custom telemetry backends.
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from contextlib import contextmanager
from abc import ABC, abstractmethod
import traceback

from .types import TelemetryCallback, AsyncTelemetryCallback, TelemetryEvent

logger = logging.getLogger(__name__)


class LogLevel(str, Enum):
    """Log levels compatible with Python logging."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogEntry:
    """Structured log entry."""
    timestamp: datetime
    level: str
    logger: str
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    exception: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "logger": self.logger,
            "message": self.message,
            "context": self.context,
            "exception": self.exception
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class LogSink(ABC):
    """Abstract base class for log sinks."""
    
    @abstractmethod
    def write(self, entry: LogEntry):
        """Write a log entry."""
        pass
    
    @abstractmethod
    def flush(self):
        """Flush buffered entries."""
        pass
    
    @abstractmethod
    def close(self):
        """Close the sink."""
        pass


class ConsoleSink(LogSink):
    """Console log sink with color support."""
    
    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[35m",   # Magenta
        "RESET": "\033[0m"
    }
    
    def __init__(self, use_colors: bool = True):
        self.use_colors = use_colors
        self._lock = threading.Lock()
    
    def write(self, entry: LogEntry):
        level = entry.level
        color = self.COLORS.get(level, "")
        reset = self.COLORS["RESET"] if self.use_colors else ""
        
        parts = [
            entry.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            f"{color}{level}{reset}",
            f"[{entry.logger}]",
            entry.message
        ]
        
        if entry.context:
            parts.append(json.dumps(entry.context))
        
        if entry.exception:
            parts.append(f"\n{entry.exception}")
        
        with self._lock:
            print(" ".join(parts))
    
    def flush(self):
        pass
    
    def close(self):
        pass


class FileSink(LogSink):
    """File-based log sink with rotation support."""
    
    def __init__(
        self,
        filename: str,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        format_json: bool = False
    ):
        self.filename = filename
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.format_json = format_json
        self._lock = threading.Lock()
        self._buffer: List[LogEntry] = []
        self._buffer_size = 0
        
        import logging.handlers
        self._handler = logging.handlers.RotatingFileHandler(
            filename,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
    
    def write(self, entry: LogEntry):
        with self._lock:
            if self.format_json:
                self._handler.emit(entry.to_json())
            else:
                line = f"{entry.timestamp.isoformat()} {entry.level} [{entry.logger}] {entry.message}"
                if entry.context:
                    line += f" {json.dumps(entry.context)}"
                if entry.exception:
                    line += f"\n{entry.exception}"
                self._handler.emit(line + "\n")
    
    def flush(self):
        with self._lock:
            self._handler.flush()
    
    def close(self):
        self._handler.close()


class TelemetrySink(ABC):
    """Abstract base class for telemetry sinks."""
    
    @abstractmethod
    def record(self, event: TelemetryEvent):
        """Record a telemetry event."""
        pass
    
    @abstractmethod
    def flush(self):
        """Flush buffered events."""
        pass


class InMemoryTelemetrySink(TelemetrySink):
    """In-memory telemetry sink with size limits."""
    
    def __init__(self, max_events: int = 10000):
        self.max_events = max_events
        self._events: List[TelemetryEvent] = []
        self._lock = threading.Lock()
    
    def record(self, event: TelemetryEvent):
        with self._lock:
            self._events.append(event)
            # Trim old events if buffer full
            if len(self._events) > self.max_events:
                self._events = self._events[-self.max_events:]
    
    def flush(self):
        pass
    
    def get_events(
        self,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[TelemetryEvent]:
        """Get recent telemetry events."""
        with self._lock:
            events = self._events
            if event_type:
                events = [e for e in events if e.event_type == event_type]
            return events[-limit:]
    
    def clear(self):
        """Clear all events."""
        with self._lock:
            self._events.clear()


class AetherTelemetryHandler:
    """
    Comprehensive telemetry and logging handler.
    
    Provides:
    - Structured logging with multiple sinks
    - Event-based telemetry
    - Performance metrics tracking
    - Request/response logging
    - Error tracking
    """
    
    def __init__(
        self,
        logger_name: str = "adk_client",
        log_level: LogLevel = LogLevel.INFO,
        enable_console: bool = True,
        enable_file: bool = False,
        log_file: Optional[str] = None,
        enable_telemetry: bool = True,
        telemetry_callback: Optional[TelemetryCallback] = None,
        async_telemetry_callback: Optional[AsyncTelemetryCallback] = None
    ):
        self.logger_name = logger_name
        self._logger = logging.getLogger(logger_name)
        self._logger.setLevel(getattr(logging, log_level.value))
        
        # Remove existing handlers
        self._logger.handlers.clear()
        
        # Setup sinks
        self._log_sinks: List[LogSink] = []
        
        if enable_console:
            self._log_sinks.append(ConsoleSink())
        
        if enable_file and log_file:
            self._log_sinks.append(FileSink(log_file))
        
        # Setup telemetry
        self._telemetry_enabled = enable_telemetry
        self._telemetry_sinks: List[TelemetrySink] = []
        self._telemetry_callback = telemetry_callback
        self._async_telemetry_callback = async_telemetry_callback
        
        if enable_telemetry:
            self._telemetry_sinks.append(InMemoryTelemetrySink())
    
    def _log(
        self,
        level: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None
    ):
        """Internal log method."""
        entry = LogEntry(
            timestamp=datetime.utcnow(),
            level=level,
            logger=self.logger_name,
            message=message,
            context=context or {},
            exception=traceback.format_exc() if exception else None
        )
        
        for sink in self._log_sinks:
            try:
                sink.write(entry)
            except Exception as e:
                print(f"Error writing to log sink: {e}")
    
    def debug(self, message: str, **context):
        """Log debug message."""
        self._log("DEBUG", message, context)
    
    def info(self, message: str, **context):
        """Log info message."""
        self._log("INFO", message, context)
    
    def warning(self, message: str, **context):
        """Log warning message."""
        self._log("WARNING", message, context)
    
    def error(self, message: str, exception: Optional[Exception] = None, **context):
        """Log error message."""
        self._log("ERROR", message, context, exception)
    
    def critical(self, message: str, exception: Optional[Exception] = None, **context):
        """Log critical message."""
        self._log("CRITICAL", message, context, exception)
    
    def record_telemetry(
        self,
        event_type: str,
        success: bool = True,
        duration_ms: Optional[float] = None,
        error: Optional[str] = None,
        **metadata
    ):
        """Record a telemetry event."""
        if not self._telemetry_enabled:
            return
        
        event = TelemetryEvent(
            event_type=event_type,
            timestamp=datetime.utcnow(),
            success=success,
            duration_ms=duration_ms,
            error=error,
            metadata=metadata
        )
        
        # Record to sinks
        for sink in self._telemetry_sinks:
            try:
                sink.record(event)
            except Exception as e:
                self._logger.error(f"Error recording telemetry: {e}")
        
        # Call callback if set
        if self._telemetry_callback:
            try:
                self._telemetry_callback(event)
            except Exception as e:
                self._logger.error(f"Error in telemetry callback: {e}")
        
        if self._async_telemetry_callback:
            asyncio.create_task(self._call_async_callback(event))
    
    async def _call_async_callback(self, event: TelemetryEvent):
        """Call async telemetry callback."""
        try:
            await self._async_telemetry_callback(event)
        except Exception as e:
            self._logger.error(f"Error in async telemetry callback: {e}")
    
    @contextmanager
    def track_request(
        self,
        operation: str,
        request_id: Optional[str] = None,
        **context
    ):
        """Context manager for tracking request performance."""
        start_time = time.time()
        
        try:
            yield
            duration_ms = (time.time() - start_time) * 1000
            self.record_telemetry(
                event_type=f"{operation}_success",
                success=True,
                duration_ms=duration_ms,
                request_id=request_id,
                **context
            )
            self.info(
                f"{operation} completed",
                duration_ms=duration_ms,
                request_id=request_id,
                **context
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.record_telemetry(
                event_type=f"{operation}_error",
                success=False,
                duration_ms=duration_ms,
                error=str(e),
                request_id=request_id,
                **context
            )
            self.error(
                f"{operation} failed",
                exception=e,
                duration_ms=duration_ms,
                request_id=request_id,
                **context
            )
            raise
    
    def get_telemetry_events(
        self,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[TelemetryEvent]:
        """Get recent telemetry events."""
        for sink in self._telemetry_sinks:
            if isinstance(sink, InMemoryTelemetrySink):
                return sink.get_events(event_type, limit)
        return []
    
    def flush(self):
        """Flush all sinks."""
        for sink in self._log_sinks:
            sink.flush()
        for sink in self._telemetry_sinks:
            sink.flush()
    
    def add_log_sink(self, sink: LogSink):
        """Add a custom log sink."""
        self._log_sinks.append(sink)
    
    def add_telemetry_sink(self, sink: TelemetrySink):
        """Add a custom telemetry sink."""
        self._telemetry_sinks.append(sink)


