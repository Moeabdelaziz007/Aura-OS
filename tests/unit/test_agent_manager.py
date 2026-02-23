"""
Unit Tests for Agent Manager Module

Tests the agent lifecycle management including boot sequence, shutdown,
and pulse monitoring for the AetherOS orchestrator.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime


# =============================================================================
# Import the module under test
# =============================================================================

from agent.orchestrator.modules.agent_manager import AgentManager


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def agent_manager(mock_bridge, mock_forge):
    """
    Create an AgentManager instance with mocked dependencies.
    """
    return AgentManager(
        bridge=mock_bridge,
        forge=mock_forge,
        drift_threshold_ms=500.0
    )


@pytest.fixture
def agent_manager_custom_threshold(mock_bridge, mock_forge):
    """
    Create an AgentManager instance with custom drift threshold.
    """
    return AgentManager(
        bridge=mock_bridge,
        forge=mock_forge,
        drift_threshold_ms=1000.0
    )


# =============================================================================
# Test: AgentManager Initialization
# =============================================================================

class TestAgentManagerInitialization:
    """Test cases for AgentManager initialization."""

    def test_initialization_with_default_threshold(self, mock_bridge, mock_forge):
        """
        Test that AgentManager initializes with default drift threshold.
        """
        manager = AgentManager(mock_bridge, mock_forge)
        assert manager.bridge == mock_bridge
        assert manager.forge == mock_forge
        assert manager.drift_threshold_ms == 500.0
        assert manager.is_running is False
        assert manager._cleanup_tasks == set()
        assert manager._max_retries == 3

    def test_initialization_with_custom_threshold(self, mock_bridge, mock_forge):
        """
        Test that AgentManager initializes with custom drift threshold.
        """
        manager = AgentManager(mock_bridge, mock_forge, drift_threshold_ms=1000.0)
        assert manager.drift_threshold_ms == 1000.0

    def test_initialization_cleanup_tasks_is_empty_set(self, mock_bridge, mock_forge):
        """
        Test that cleanup tasks is initialized as an empty set.
        """
        manager = AgentManager(mock_bridge, mock_forge)
        assert isinstance(manager._cleanup_tasks, set)
        assert len(manager._cleanup_tasks) == 0


# =============================================================================
# Test: Boot Sequence
# =============================================================================

class TestBootSequence:
    """Test cases for the boot sequence functionality."""

    @pytest.mark.asyncio
    async def test_boot_sequence_success(self, agent_manager):
        """
        Test successful boot sequence with DNA loading and forge ignition.
        """
        await agent_manager.boot_sequence()
        
        # Verify DNA was loaded
        agent_manager.bridge.load_dna_async.assert_called_once()
        
        # Verify forge was ignited (entered async context)
        agent_manager.forge.__aenter__.assert_called_once()
        
        # Verify is_running is set to True
        assert agent_manager.is_running is True
        
        # Verify pulse monitor task was created
        assert len(agent_manager._cleanup_tasks) == 1

    @pytest.mark.asyncio
    async def test_boot_sequence_with_dna_load_failure(self, agent_manager):
        """
        Test boot sequence handles DNA load failure gracefully.
        """
        agent_manager.bridge.load_dna_async = AsyncMock(side_effect=Exception("DNA load failed"))
        
        with pytest.raises(Exception, match="DNA load failed"):
            await agent_manager.boot_sequence()

    @pytest.mark.asyncio
    async def test_boot_sequence_with_forge_ignition_failure(self, agent_manager):
        """
        Test boot sequence handles forge ignition failure gracefully.
        """
        agent_manager.forge.__aenter__ = AsyncMock(side_effect=Exception("Forge ignition failed"))
        
        with pytest.raises(Exception, match="Forge ignition failed"):
            await agent_manager.boot_sequence()

    @pytest.mark.asyncio
    async def test_boot_sequence_creates_pulse_monitor_task(self, agent_manager):
        """
        Test that boot sequence creates and tracks the pulse monitor task.
        """
        await agent_manager.boot_sequence()
        
        assert len(agent_manager._cleanup_tasks) == 1
        task = list(agent_manager._cleanup_tasks)[0]
        assert task.get_name() == "pulse_monitor"


# =============================================================================
# Test: Pulse Monitor
# =============================================================================

class TestPulseMonitor:
    """Test cases for the pulse monitor functionality."""

    @pytest.mark.asyncio
    async def test_pulse_monitor_runs_continuously(self, agent_manager):
        """
        Test that pulse monitor runs in a continuous loop.
        """
        # Create a task that will be cancelled after a short delay
        monitor_task = asyncio.create_task(agent_manager.pulse_monitor(interval=0.01))
        
        # Let it run for a bit
        await asyncio.sleep(0.05)
        
        # Cancel the task
        monitor_task.cancel()
        
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_pulse_monitor_with_custom_interval(self, agent_manager):
        """
        Test pulse monitor with custom interval.
        """
        monitor_task = asyncio.create_task(agent_manager.pulse_monitor(interval=0.02))
        
        # Let it run for a bit
        await asyncio.sleep(0.06)
        
        monitor_task.cancel()
        
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_pulse_monitor_can_be_cancelled(self, agent_manager):
        """
        Test that pulse monitor can be cancelled gracefully.
        """
        monitor_task = asyncio.create_task(agent_manager.pulse_monitor(interval=0.01))
        
        # Cancel immediately
        monitor_task.cancel()
        
        with pytest.raises(asyncio.CancelledError):
            await monitor_task


# =============================================================================
# Test: Shutdown
# =============================================================================

class TestShutdown:
    """Test cases for the shutdown functionality."""

    @pytest.mark.asyncio
    async def test_shutdown_success(self, agent_manager):
        """
        Test successful shutdown with resource cleanup.
        """
        # Set up running state
        agent_manager.is_running = True
        
        # Create a real async task that will be cancelled
        async def dummy_task():
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                raise
        
        mock_task = asyncio.create_task(dummy_task())
        agent_manager._cleanup_tasks.add(mock_task)
        
        await agent_manager.shutdown()
        
        # Verify is_running is set to False
        assert agent_manager.is_running is False
        
        # Verify cleanup tasks are cleared
        assert len(agent_manager._cleanup_tasks) == 0

    @pytest.mark.asyncio
    async def test_shutdown_with_no_cleanup_tasks(self, agent_manager):
        """
        Test shutdown when there are no cleanup tasks.
        """
        agent_manager.is_running = True
        
        await agent_manager.shutdown()
        
        assert agent_manager.is_running is False

    @pytest.mark.asyncio
    async def test_shutdown_with_already_done_task(self, agent_manager):
        """
        Test shutdown with a task that is already done.
        """
        agent_manager.is_running = True
        
        # Create a task that completes immediately
        async def done_task():
            pass
        mock_task = asyncio.create_task(done_task())
        await mock_task  # Wait for it to complete
        
        agent_manager._cleanup_tasks.add(mock_task)
        
        await agent_manager.shutdown()
        
        # Task should not be cancelled if already done
        assert mock_task.done()

    @pytest.mark.asyncio
    async def test_shutdown_handles_cancelled_error_gracefully(self, agent_manager):
        """
        Test shutdown handles asyncio.CancelledError when cancelling tasks.
        """
        agent_manager.is_running = True
        
        # Create a real async task that will be cancelled
        async def cancellable_task():
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                raise
        
        mock_task = asyncio.create_task(cancellable_task())
        agent_manager._cleanup_tasks.add(mock_task)
        
        # Should not raise exception
        await agent_manager.shutdown()
        
        assert agent_manager.is_running is False

    @pytest.mark.asyncio
    async def test_shutdown_without_bridge_close_method(self, agent_manager):
        """
        Test shutdown when bridge doesn't have a close method.
        """
        agent_manager.is_running = True
        # Create a mock without close method
        agent_manager.bridge = Mock(spec=[])  # Empty spec means no attributes
        
        # Should not raise exception
        await agent_manager.shutdown()
        
        assert agent_manager.is_running is False

    @pytest.mark.asyncio
    async def test_shutdown_without_forge_exit_method(self, agent_manager):
        """
        Test shutdown when forge doesn't have an __aexit__ method.
        """
        agent_manager.is_running = True
        # Create a mock without __aexit__ method
        agent_manager.forge = Mock(spec=[])  # Empty spec means no attributes
        
        # Should not raise exception
        await agent_manager.shutdown()
        
        assert agent_manager.is_running is False


# =============================================================================
# Test: Cleanup Task Management
# =============================================================================

class TestCleanupTaskManagement:
    """Test cases for cleanup task management."""

    def test_add_cleanup_task(self, agent_manager):
        """
        Test adding a task to the cleanup set.
        """
        mock_task = Mock()
        agent_manager.add_cleanup_task(mock_task)
        
        assert mock_task in agent_manager._cleanup_tasks

    def test_add_multiple_cleanup_tasks(self, agent_manager):
        """
        Test adding multiple tasks to the cleanup set.
        """
        task1 = Mock()
        task2 = Mock()
        task3 = Mock()
        
        agent_manager.add_cleanup_task(task1)
        agent_manager.add_cleanup_task(task2)
        agent_manager.add_cleanup_task(task3)
        
        assert len(agent_manager._cleanup_tasks) == 3
        assert task1 in agent_manager._cleanup_tasks
        assert task2 in agent_manager._cleanup_tasks
        assert task3 in agent_manager._cleanup_tasks

    def test_remove_cleanup_task(self, agent_manager):
        """
        Test removing a task from the cleanup set.
        """
        mock_task = Mock()
        agent_manager.add_cleanup_task(mock_task)
        
        agent_manager.remove_cleanup_task(mock_task)
        
        assert mock_task not in agent_manager._cleanup_tasks

    def test_remove_nonexistent_cleanup_task(self, agent_manager):
        """
        Test removing a task that doesn't exist in the cleanup set.
        """
        mock_task = Mock()
        
        # Should not raise exception
        agent_manager.remove_cleanup_task(mock_task)
        
        assert len(agent_manager._cleanup_tasks) == 0

    def test_remove_cleanup_task_discards_not_removes(self, agent_manager):
        """
        Test that remove_cleanup_task uses discard (no error if not present).
        """
        mock_task = Mock()
        
        # Using discard should not raise KeyError
        agent_manager._cleanup_tasks.discard(mock_task)
        
        assert len(agent_manager._cleanup_tasks) == 0


# =============================================================================
# Test: Edge Cases and Error Handling
# =============================================================================

class TestEdgeCases:
    """Test cases for edge cases and error handling."""

    def test_agent_manager_with_none_bridge(self):
        """
        Test AgentManager handles None bridge gracefully.
        """
        forge = Mock()
        manager = AgentManager(None, forge)
        assert manager.bridge is None

    def test_agent_manager_with_none_forge(self):
        """
        Test AgentManager handles None forge gracefully.
        """
        bridge = Mock()
        manager = AgentManager(bridge, None)
        assert manager.forge is None

    def test_drift_threshold_negative_value(self, mock_bridge, mock_forge):
        """
        Test AgentManager with negative drift threshold.
        """
        manager = AgentManager(mock_bridge, mock_forge, drift_threshold_ms=-100.0)
        assert manager.drift_threshold_ms == -100.0

    def test_drift_threshold_zero_value(self, mock_bridge, mock_forge):
        """
        Test AgentManager with zero drift threshold.
        """
        manager = AgentManager(mock_bridge, mock_forge, drift_threshold_ms=0.0)
        assert manager.drift_threshold_ms == 0.0

    def test_add_same_cleanup_task_twice(self, agent_manager):
        """
        Test adding the same task twice (set behavior).
        """
        mock_task = Mock()
        agent_manager.add_cleanup_task(mock_task)
        agent_manager.add_cleanup_task(mock_task)
        
        # Set should only contain one instance
        assert len(agent_manager._cleanup_tasks) == 1

    @pytest.mark.asyncio
    async def test_shutdown_multiple_times(self, agent_manager):
        """
        Test that shutdown can be called multiple times safely.
        """
        agent_manager.is_running = True
        
        await agent_manager.shutdown()
        await agent_manager.shutdown()
        await agent_manager.shutdown()
        
        assert agent_manager.is_running is False

    @pytest.mark.asyncio
    async def test_boot_sequence_after_shutdown(self, agent_manager):
        """
        Test that boot sequence can be called after shutdown.
        """
        # First boot
        await agent_manager.boot_sequence()
        assert agent_manager.is_running is True
        
        # Shutdown
        await agent_manager.shutdown()
        assert agent_manager.is_running is False
        
        # Boot again
        await agent_manager.boot_sequence()
        assert agent_manager.is_running is True
