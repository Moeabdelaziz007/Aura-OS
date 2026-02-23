"""
Telemetry Handler Module

Handles telemetry and anomaly monitoring for the AetherOS orchestrator.

Classes:
    TelemetryHandler: Manages anomaly logging and telemetry operations
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..aether_evolve import AetherNeuralMonitor


class TelemetryHandler:
    """
    Manages telemetry and anomaly monitoring.

    Responsible for:
    - Logging anomalies from various components
    - Providing telemetry data access
    - Coordinating with AetherEvolve for autonomous healing
    """

    def __init__(self, monitor: "AetherNeuralMonitor"):
        """
        Initialize the Telemetry Handler.

        Args:
            monitor: The AetherNeuralMonitor from aether_evolve for anomaly tracking
        """
        self.monitor = monitor

    def log_anomaly(self, component: str, error_type: str, message: str) -> None:
        """
        Log an anomaly for tracking and potential autonomous healing.

        Args:
            component: The component where the anomaly occurred
            error_type: The type of error/anomaly
            message: Detailed message about the anomaly
        """
        self.monitor.log_anomaly(component, error_type, message)

    def get_anomaly_log(self) -> list:
        """
        Get the current anomaly log.

        Returns:
            List of logged anomalies
        """
        return list(self.monitor.anomaly_log)

    def get_anomaly_count(self) -> int:
        """
        Get the total count of logged anomalies.

        Returns:
            Number of anomalies logged
        """
        return len(self.monitor.anomaly_log)

    def clear_anomaly_log(self) -> None:
        """Clear the anomaly log."""
        self.monitor.anomaly_log.clear()

    def get_recent_anomalies(self, limit: int = 10) -> list:
        """
        Get the most recent anomalies.

        Args:
            limit: Maximum number of recent anomalies to return

        Returns:
            List of recent anomalies (most recent first)
        """
        return self.monitor.anomaly_log[-limit:] if self.monitor.anomaly_log else []

    def get_anomalies_by_component(self, component: str) -> list:
        """
        Get all anomalies for a specific component.

        Args:
            component: The component name to filter by

        Returns:
            List of anomalies for the specified component
        """
        return [
            anomaly for anomaly in self.monitor.anomaly_log
            if anomaly.get("component") == component
        ]

    def get_anomaly_summary(self) -> dict:
        """
        Get a summary of anomalies grouped by component and error type.

        Returns:
            Dictionary with anomaly counts grouped by component and error type
        """
        summary = {}
        for anomaly in self.monitor.anomaly_log:
            component = anomaly.get("component", "unknown")
            error_type = anomaly.get("error_type", "unknown")

            if component not in summary:
                summary[component] = {}

            if error_type not in summary[component]:
                summary[component][error_type] = 0

            summary[component][error_type] += 1

        return summary
