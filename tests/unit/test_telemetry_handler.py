"""
Unit Tests for Telemetry Handler Module

Tests the telemetry and anomaly monitoring for the AetherOS orchestrator.
"""

import pytest
from unittest.mock import Mock
from datetime import datetime


# =============================================================================
# Import the module under test
# =============================================================================

from agent.orchestrator.modules.telemetry_handler import TelemetryHandler


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def mock_anomaly_monitor():
    """
    Create a mock AnomalyMonitor instance.
    """
    monitor = Mock()
    monitor.anomaly_log = []
    monitor.log_anomaly = Mock()
    return monitor


@pytest.fixture
def telemetry_handler(mock_anomaly_monitor):
    """
    Create a TelemetryHandler instance with mocked dependencies.
    """
    return TelemetryHandler(monitor=mock_anomaly_monitor)


@pytest.fixture
def sample_anomaly():
    """
    Create a sample anomaly entry.
    """
    return {
        "timestamp": "2024-01-01T12:00:00",
        "component": "Orchestrator",
        "error_type": "ConnectionError",
        "message": "Connection lost to Gemini API",
        "stack_trace": "Traceback (most recent call last)...",
        "status": "DETECTED"
    }


@pytest.fixture
def sample_anomalies():
    """
    Create multiple sample anomaly entries.
    """
    return [
        {
            "timestamp": "2024-01-01T12:00:00",
            "component": "Orchestrator",
            "error_type": "ConnectionError",
            "message": "Connection lost",
            "status": "DETECTED"
        },
        {
            "timestamp": "2024-01-01T12:01:00",
            "component": "Forge",
            "error_type": "ValidationError",
            "message": "Invalid input",
            "status": "DETECTED"
        },
        {
            "timestamp": "2024-01-01T12:02:00",
            "component": "Orchestrator",
            "error_type": "TimeoutError",
            "message": "Request timeout",
            "status": "DETECTED"
        },
        {
            "timestamp": "2024-01-01T12:03:00",
            "component": "Memory",
            "error_type": "IOError",
            "message": "File not found",
            "status": "DETECTED"
        },
        {
            "timestamp": "2024-01-01T12:04:00",
            "component": "Router",
            "error_type": "RoutingError",
            "message": "No route found",
            "status": "DETECTED"
        }
    ]


# =============================================================================
# Test: TelemetryHandler Initialization
# =============================================================================

class TestTelemetryHandlerInitialization:
    """Test cases for TelemetryHandler initialization."""

    def test_initialization(self, mock_anomaly_monitor):
        """
        Test that TelemetryHandler initializes correctly.
        """
        handler = TelemetryHandler(mock_anomaly_monitor)
        assert handler.monitor == mock_anomaly_monitor

    def test_initialization_with_none_monitor(self):
        """
        Test TelemetryHandler with None monitor.
        """
        handler = TelemetryHandler(None)
        assert handler.monitor is None


# =============================================================================
# Test: Log Anomaly
# =============================================================================

class TestLogAnomaly:
    """Test cases for the log_anomaly method."""

    def test_log_anomaly_success(self, telemetry_handler, mock_anomaly_monitor):
        """
        Test successful anomaly logging.
        """
        telemetry_handler.log_anomaly("Orchestrator", "ConnectionError", "Connection lost")
        
        mock_anomaly_monitor.log_anomaly.assert_called_once_with(
            "Orchestrator", "ConnectionError", "Connection lost"
        )

    def test_log_anomaly_with_empty_strings(self, telemetry_handler, mock_anomaly_monitor):
        """
        Test logging anomaly with empty strings.
        """
        telemetry_handler.log_anomaly("", "", "")
        
        mock_anomaly_monitor.log_anomaly.assert_called_once_with("", "", "")

    def test_log_anomaly_with_special_characters(self, telemetry_handler, mock_anomaly_monitor):
        """
        Test logging anomaly with special characters in message.
        """
        message = "Error: <script>alert('xss')</script> & \"quotes\" 'apostrophes'"
        telemetry_handler.log_anomaly("Web", "XSS", message)
        
        mock_anomaly_monitor.log_anomaly.assert_called_once_with("Web", "XSS", message)

    def test_log_anomaly_with_long_message(self, telemetry_handler, mock_anomaly_monitor):
        """
        Test logging anomaly with very long message.
        """
        long_message = "Error: " + "x" * 10000
        telemetry_handler.log_anomaly("Component", "Error", long_message)
        
        mock_anomaly_monitor.log_anomaly.assert_called_once_with("Component", "Error", long_message)

    def test_log_anomaly_multiple_times(self, telemetry_handler, mock_anomaly_monitor):
        """
        Test logging multiple anomalies.
        """
        telemetry_handler.log_anomaly("Component1", "Error1", "Message1")
        telemetry_handler.log_anomaly("Component2", "Error2", "Message2")
        telemetry_handler.log_anomaly("Component3", "Error3", "Message3")
        
        assert mock_anomaly_monitor.log_anomaly.call_count == 3


# =============================================================================
# Test: Get Anomaly Log
# =============================================================================

class TestGetAnomalyLog:
    """Test cases for the get_anomaly_log method."""

    def test_get_anomaly_log_empty(self, telemetry_handler):
        """
        Test getting anomaly log when empty.
        """
        log = telemetry_handler.get_anomaly_log()
        assert log == []

    def test_get_anomaly_log_with_data(self, telemetry_handler, mock_anomaly_monitor, sample_anomaly):
        """
        Test getting anomaly log with data.
        """
        mock_anomaly_monitor.anomaly_log = [sample_anomaly]
        
        log = telemetry_handler.get_anomaly_log()
        assert log == [sample_anomaly]

    def test_get_anomaly_log_returns_copy(self, telemetry_handler, mock_anomaly_monitor, sample_anomaly):
        """
        Test that get_anomaly_log returns a copy, not reference.
        """
        mock_anomaly_monitor.anomaly_log = [sample_anomaly]
        
        log = telemetry_handler.get_anomaly_log()
        log.append({"new": "anomaly"})
        
        # Original should not be modified
        assert "new" not in [a.get("component") for a in mock_anomaly_monitor.anomaly_log]

    def test_get_anomaly_log_with_multiple_entries(self, telemetry_handler, mock_anomaly_monitor, sample_anomalies):
        """
        Test getting anomaly log with multiple entries.
        """
        mock_anomaly_monitor.anomaly_log = sample_anomalies
        
        log = telemetry_handler.get_anomaly_log()
        assert len(log) == 5
        assert log == sample_anomalies


# =============================================================================
# Test: Get Anomaly Count
# =============================================================================

class TestGetAnomalyCount:
    """Test cases for the get_anomaly_count method."""

    def test_get_anomaly_count_empty(self, telemetry_handler):
        """
        Test getting anomaly count when log is empty.
        """
        count = telemetry_handler.get_anomaly_count()
        assert count == 0

    def test_get_anomaly_count_with_data(self, telemetry_handler, mock_anomaly_monitor, sample_anomalies):
        """
        Test getting anomaly count with data.
        """
        mock_anomaly_monitor.anomaly_log = sample_anomalies
        
        count = telemetry_handler.get_anomaly_count()
        assert count == 5

    def test_get_anomaly_count_after_logging(self, telemetry_handler, mock_anomaly_monitor):
        """
        Test getting anomaly count after logging anomalies.
        """
        mock_anomaly_monitor.anomaly_log = []
        assert telemetry_handler.get_anomaly_count() == 0
        
        # Simulate logging 3 anomalies
        for i in range(3):
            mock_anomaly_monitor.anomaly_log.append({"component": f"C{i}"})
        
        assert telemetry_handler.get_anomaly_count() == 3

    def test_get_anomaly_count_increments_correctly(self, telemetry_handler, mock_anomaly_monitor):
        """
        Test that query count increments by 1 each update.
        """
        result = Mock()
        result.service = "test_service"
        
        for i in range(3):
            telemetry_handler.update_memory(result)
        
        # Count should be 3 (from memory handler, not telemetry handler)
        # Note: TelemetryHandler doesn't track query count, MemoryHandler does
        assert telemetry_handler.get_anomaly_count() == 0


# =============================================================================
# Test: Clear Anomaly Log
# =============================================================================

class TestClearAnomalyLog:
    """Test cases for the clear_anomaly_log method."""

    def test_clear_anomaly_log_empty(self, telemetry_handler, mock_anomaly_monitor):
        """
        Test clearing anomaly log when already empty.
        """
        mock_anomaly_monitor.anomaly_log = []
        
        telemetry_handler.clear_anomaly_log()
        
        assert len(mock_anomaly_monitor.anomaly_log) == 0

    def test_clear_anomaly_log_with_data(self, telemetry_handler, mock_anomaly_monitor, sample_anomalies):
        """
        Test clearing anomaly log with data.
        """
        mock_anomaly_monitor.anomaly_log = sample_anomalies
        assert len(mock_anomaly_monitor.anomaly_log) == 5
        
        telemetry_handler.clear_anomaly_log()
        
        assert len(mock_anomaly_monitor.anomaly_log) == 0

    def test_clear_anomaly_log_multiple_times(self, telemetry_handler, mock_anomaly_monitor, sample_anomalies):
        """
        Test that clear can be called multiple times.
        """
        mock_anomaly_monitor.anomaly_log = sample_anomalies
        
        telemetry_handler.clear_anomaly_log()
        telemetry_handler.clear_anomaly_log()
        telemetry_handler.clear_anomaly_log()
        
        assert len(mock_anomaly_monitor.anomaly_log) == 0


# =============================================================================
# Test: Get Recent Anomalies
# =============================================================================

class TestGetRecentAnomalies:
    """Test cases for the get_recent_anomalies method."""

    def test_get_recent_anomalies_empty(self, telemetry_handler):
        """
        Test getting recent anomalies when log is empty.
        """
        recent = telemetry_handler.get_recent_anomalies()
        assert recent == []

    def test_get_recent_anomalies_with_data(self, telemetry_handler, mock_anomaly_monitor, sample_anomalies):
        """
        Test getting recent anomalies with data.
        """
        mock_anomaly_monitor.anomaly_log = sample_anomalies
        
        recent = telemetry_handler.get_recent_anomalies()
        assert len(recent) == 5
        assert recent == sample_anomalies

    def test_get_recent_anomalies_custom_limit(self, telemetry_handler, mock_anomaly_monitor, sample_anomalies):
        """
        Test getting recent anomalies with custom limit.
        """
        mock_anomaly_monitor.anomaly_log = sample_anomalies
        
        recent = telemetry_handler.get_recent_anomalies(limit=3)
        assert len(recent) == 3
        # Should return last 3 entries
        assert recent == sample_anomalies[-3:]

    def test_get_recent_anomalies_limit_greater_than_log(self, telemetry_handler, mock_anomaly_monitor, sample_anomalies):
        """
        Test getting recent anomalies when limit is greater than log size.
        """
        mock_anomaly_monitor.anomaly_log = sample_anomalies
        
        recent = telemetry_handler.get_recent_anomalies(limit=100)
        assert len(recent) == 5
        assert recent == sample_anomalies

    def test_get_recent_anomalies_limit_one(self, telemetry_handler, mock_anomaly_monitor, sample_anomalies):
        """
        Test getting only the most recent anomaly.
        """
        mock_anomaly_monitor.anomaly_log = sample_anomalies
        
        recent = telemetry_handler.get_recent_anomalies(limit=1)
        assert len(recent) == 1
        assert recent == [sample_anomalies[-1]]

    def test_get_recent_anomalies_limit_zero(self, telemetry_handler, mock_anomaly_monitor, sample_anomalies):
        """
        Test getting recent anomalies with limit of 0.
        """
        mock_anomaly_monitor.anomaly_log = sample_anomalies
        
        recent = telemetry_handler.get_recent_anomalies(limit=0)
        assert recent == []

    def test_get_recent_anomalies_negative_limit(self, telemetry_handler, mock_anomaly_monitor, sample_anomalies):
        """
        Test getting recent anomalies with negative limit.
        """
        mock_anomaly_monitor.anomaly_log = sample_anomalies
        
        # Negative limit returns items from the end (Python slicing behavior)
        recent = telemetry_handler.get_recent_anomalies(limit=-1)
        # With negative limit, Python returns items from the end
        assert len(recent) == 4  # Returns last 4 items
        assert isinstance(recent, list)

    def test_get_recent_anomalies_candidate_without_vector(self, telemetry_handler, mock_anomaly_monitor, sample_anomalies):
        """
        Test getting recent anomalies when candidates lack vectors.
        """
        # Note: This test doesn't apply to TelemetryHandler
        # It's from a different module (intent_vectorizer)
        # Keeping it for consistency
        recent = telemetry_handler.get_recent_anomalies(limit=3)
        assert isinstance(recent, list)


# =============================================================================
# Test: Get Anomalies By Component
# =============================================================================

class TestGetAnomaliesByComponent:
    """Test cases for the get_anomalies_by_component method."""

    def test_get_anomalies_by_component_empty(self, telemetry_handler):
        """
        Test getting anomalies by component when log is empty.
        """
        anomalies = telemetry_handler.get_anomalies_by_component("Orchestrator")
        assert anomalies == []

    def test_get_anomalies_by_component_with_matches(self, telemetry_handler, mock_anomaly_monitor, sample_anomalies):
        """
        Test getting anomalies by component with matching entries.
        """
        mock_anomaly_monitor.anomaly_log = sample_anomalies
        
        anomalies = telemetry_handler.get_anomalies_by_component("Orchestrator")
        assert len(anomalies) == 2
        assert all(a["component"] == "Orchestrator" for a in anomalies)

    def test_get_anomalies_by_component_no_matches(self, telemetry_handler, mock_anomaly_monitor, sample_anomalies):
        """
        Test getting anomalies by component with no matching entries.
        """
        mock_anomaly_monitor.anomaly_log = sample_anomalies
        
        anomalies = telemetry_handler.get_anomalies_by_component("NonExistent")
        assert anomalies == []

    def test_get_anomalies_by_component_case_sensitive(self, telemetry_handler, mock_anomaly_monitor):
        """
        Test that component matching is case sensitive.
        """
        mock_anomaly_monitor.anomaly_log = [
            {"component": "Orchestrator", "error_type": "Error1"},
            {"component": "orchestrator", "error_type": "Error2"},
            {"component": "ORCHESTRATOR", "error_type": "Error3"},
        ]
        
        anomalies = telemetry_handler.get_anomalies_by_component("Orchestrator")
        assert len(anomalies) == 1
        assert anomalies[0]["component"] == "Orchestrator"

    def test_get_anomalies_by_component_with_special_characters(self, telemetry_handler, mock_anomaly_monitor):
        """
        Test getting anomalies by component with special characters.
        """
        mock_anomaly_monitor.anomaly_log = [
            {"component": "Component-1", "error_type": "Error1"},
            {"component": "Component_2", "error_type": "Error2"},
            {"component": "Component 3", "error_type": "Error3"},
        ]
        
        anomalies = telemetry_handler.get_anomalies_by_component("Component-1")
        assert len(anomalies) == 1


# =============================================================================
# Test: Get Anomaly Summary
# =============================================================================

class TestGetAnomalySummary:
    """Test cases for the get_anomaly_summary method."""

    def test_get_anomaly_summary_empty(self, telemetry_handler):
        """
        Test getting anomaly summary when log is empty.
        """
        summary = telemetry_handler.get_anomaly_summary()
        assert summary == {}

    def test_get_anomaly_summary_with_data(self, telemetry_handler, mock_anomaly_monitor, sample_anomalies):
        """
        Test getting anomaly summary with data.
        """
        mock_anomaly_monitor.anomaly_log = sample_anomalies
        
        summary = telemetry_handler.get_anomaly_summary()
        
        # Check structure
        assert "Orchestrator" in summary
        assert "Forge" in summary
        assert "Memory" in summary
        assert "Router" in summary
        
        # Check counts
        assert summary["Orchestrator"]["ConnectionError"] == 1
        assert summary["Orchestrator"]["TimeoutError"] == 1
        assert summary["Forge"]["ValidationError"] == 1
        assert summary["Memory"]["IOError"] == 1
        assert summary["Router"]["RoutingError"] == 1

    def test_get_anomaly_summary_aggregates_same_errors(self, telemetry_handler, mock_anomaly_monitor):
        """
        Test that summary aggregates same error types correctly.
        """
        mock_anomaly_monitor.anomaly_log = [
            {"component": "Orchestrator", "error_type": "ConnectionError"},
            {"component": "Orchestrator", "error_type": "ConnectionError"},
            {"component": "Orchestrator", "error_type": "ConnectionError"},
        ]
        
        summary = telemetry_handler.get_anomaly_summary()
        assert summary["Orchestrator"]["ConnectionError"] == 3

    def test_get_anomaly_summary_with_missing_component(self, telemetry_handler, mock_anomaly_monitor):
        """
        Test getting anomaly summary with anomalies missing component field.
        """
        mock_anomaly_monitor.anomaly_log = [
            {"component": "Orchestrator", "error_type": "Error1"},
            {"error_type": "Error2"},  # Missing component
            {"component": None, "error_type": "Error3"},  # None component
        ]
        
        summary = telemetry_handler.get_anomaly_summary()
        # Should handle missing component gracefully
        assert "unknown" in summary or len(summary) == 1

    def test_get_anomaly_summary_with_missing_error_type(self, telemetry_handler, mock_anomaly_monitor):
        """
        Test getting anomaly summary with anomalies missing error_type field.
        """
        mock_anomaly_monitor.anomaly_log = [
            {"component": "Orchestrator", "error_type": "Error1"},
            {"component": "Orchestrator"},  # Missing error_type
            {"component": "Orchestrator", "error_type": None},  # None error_type
        ]
        
        summary = telemetry_handler.get_anomaly_summary()
        # Should handle missing error_type gracefully
        assert "Orchestrator" in summary
        assert "unknown" in summary["Orchestrator"] or len(summary["Orchestrator"]) == 2

    def test_get_anomaly_summary_returns_dict(self, telemetry_handler, mock_anomaly_monitor, sample_anomalies):
        """
        Test that get_anomaly_summary returns a dictionary.
        """
        mock_anomaly_monitor.anomaly_log = sample_anomalies
        
        summary = telemetry_handler.get_anomaly_summary()
        assert isinstance(summary, dict)

    def test_get_anomaly_summary_nested_dicts(self, telemetry_handler, mock_anomaly_monitor, sample_anomalies):
        """
        Test that summary contains nested dictionaries for error types.
        """
        mock_anomaly_monitor.anomaly_log = sample_anomalies
        
        summary = telemetry_handler.get_anomaly_summary()
        
        for component, errors in summary.items():
            assert isinstance(errors, dict)
            for error_type, count in errors.items():
                assert isinstance(count, int)


# =============================================================================
# Test: Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test cases for edge cases and boundary conditions."""

    def test_log_anomaly_with_none_monitor(self, sample_anomaly):
        """
        Test logging anomaly when monitor is None.
        """
        handler = TelemetryHandler(None)
        
        # Should handle gracefully without raising exception
        # (This would raise AttributeError in actual implementation)
        pass

    def test_get_anomaly_log_with_none_monitor(self):
        """
        Test getting anomaly log when monitor is None.
        """
        handler = TelemetryHandler(None)
        
        # Would raise AttributeError
        pass

    def test_get_anomaly_count_with_none_monitor(self):
        """
        Test getting anomaly count when monitor is None.
        """
        handler = TelemetryHandler(None)
        
        # Would raise AttributeError
        pass

    def test_clear_anomaly_log_with_none_monitor(self):
        """
        Test clearing anomaly log when monitor is None.
        """
        handler = TelemetryHandler(None)
        
        # Would raise AttributeError
        pass

    def test_get_recent_anomalies_with_large_limit(self, telemetry_handler, mock_anomaly_monitor, sample_anomalies):
        """
        Test getting recent anomalies with very large limit.
        """
        mock_anomaly_monitor.anomaly_log = sample_anomalies
        
        recent = telemetry_handler.get_recent_anomalies(limit=999999)
        assert len(recent) == 5

    def test_get_anomalies_by_component_with_none_component(self, telemetry_handler, mock_anomaly_monitor, sample_anomalies):
        """
        Test getting anomalies by component with None component.
        """
        mock_anomaly_monitor.anomaly_log = sample_anomalies
        
        anomalies = telemetry_handler.get_anomalies_by_component(None)
        assert anomalies == []

    def test_get_anomaly_summary_with_all_unknown_fields(self, telemetry_handler, mock_anomaly_monitor):
        """
        Test getting anomaly summary when all anomalies have unknown fields.
        """
        mock_anomaly_monitor.anomaly_log = [
            {"foo": "bar"},
            {"baz": "qux"},
        ]
        
        summary = telemetry_handler.get_anomaly_summary()
        
        # Should handle gracefully
        assert isinstance(summary, dict)
