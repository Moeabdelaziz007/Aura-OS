"""
Unit Tests for Memory Handler Module

Tests the memory operations and signal management for the AetherOS orchestrator.
"""

import pytest
from unittest.mock import Mock


# =============================================================================
# Import the module under test
# =============================================================================

from agent.orchestrator.modules.memory_handler import MemoryHandler
from agent.forge.constraint_solver import MemorySignal
from agent.forge.models import ForgeResult


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def memory_signal():
    """
    Create a MemorySignal instance for testing.
    """
    return MemorySignal(
        recent_services=[],
        recent_assets=[],
        last_action=None,
        query_count_1h=0
    )


@pytest.fixture
def memory_handler(memory_signal):
    """
    Create a MemoryHandler instance with mocked dependencies.
    """
    return MemoryHandler(memory_signal=memory_signal)


@pytest.fixture
def coingecko_forge_result():
    """
    Create a ForgeResult for CoinGecko service.
    """
    return ForgeResult(
        success=True,
        service="coingecko",
        data={"BTC": {"price": 50000, "change": 2.5}, "trend_data": []},
        ascii_visual="BTC: $50,000 (+2.5%)",
        error=None
    )


@pytest.fixture
def github_forge_result():
    """
    Create a ForgeResult for GitHub service.
    """
    return ForgeResult(
        success=True,
        service="github",
        data={"Query": "aetheros", "stars": 100, "forks": 20},
        ascii_visual="⭐ aetheros: 100 stars",
        error=None
    )


@pytest.fixture
def weather_forge_result():
    """
    Create a ForgeResult for Weather service.
    """
    return ForgeResult(
        success=True,
        service="weather",
        data={"City": "Cairo", "Temperature": 30, "Condition": "Sunny"},
        ascii_visual="🌤️ Cairo: 30°C, Sunny",
        error=None
    )


@pytest.fixture
def forge_result_with_none_data():
    """
    Create a ForgeResult with None data.
    """
    return ForgeResult(
        success=True,
        service="unknown",
        data=None,
        ascii_visual=None,
        error=None
    )


@pytest.fixture
def forge_result_with_empty_data():
    """
    Create a ForgeResult with empty data dict.
    """
    return ForgeResult(
        success=True,
        service="unknown",
        data={},
        ascii_visual=None,
        error=None
    )


# =============================================================================
# Test: MemoryHandler Initialization
# =============================================================================

class TestMemoryHandlerInitialization:
    """Test cases for MemoryHandler initialization."""

    def test_initialization(self, memory_signal):
        """
        Test that MemoryHandler initializes correctly.
        """
        handler = MemoryHandler(memory_signal)
        assert handler.memory_signal == memory_signal

    def test_initialization_with_none_memory_signal(self):
        """
        Test MemoryHandler with None memory signal.
        """
        handler = MemoryHandler(None)
        assert handler.memory_signal is None


# =============================================================================
# Test: Update Memory
# =============================================================================

class TestUpdateMemory:
    """Test cases for the update_memory method."""

    def test_update_memory_with_coingecko_result(self, memory_handler, coingecko_forge_result):
        """
        Test updating memory with CoinGecko result.
        """
        memory_handler.update_memory(coingecko_forge_result)
        
        assert "coingecko" in memory_handler.memory_signal.recent_services
        assert "BTC" in memory_handler.memory_signal.recent_assets
        assert memory_handler.memory_signal.last_action == "coingecko"
        assert memory_handler.memory_signal.query_count_1h == 1

    def test_update_memory_with_github_result(self, memory_handler, github_forge_result):
        """
        Test updating memory with GitHub result.
        """
        memory_handler.update_memory(github_forge_result)
        
        assert "github" in memory_handler.memory_signal.recent_services
        assert "aetheros" in memory_handler.memory_signal.recent_assets
        assert memory_handler.memory_signal.last_action == "github"
        assert memory_handler.memory_signal.query_count_1h == 1

    def test_update_memory_with_weather_result(self, memory_handler, weather_forge_result):
        """
        Test updating memory with Weather result.
        """
        memory_handler.update_memory(weather_forge_result)
        
        assert "weather" in memory_handler.memory_signal.recent_services
        assert "Cairo" in memory_handler.memory_signal.recent_assets
        assert memory_handler.memory_signal.last_action == "weather"
        assert memory_handler.memory_signal.query_count_1h == 1

    def test_update_memory_with_none_data(self, memory_handler, forge_result_with_none_data):
        """
        Test updating memory with None data.
        """
        memory_handler.update_memory(forge_result_with_none_data)
        
        assert "unknown" in memory_handler.memory_signal.recent_services
        assert "unknown" in memory_handler.memory_signal.recent_assets
        assert memory_handler.memory_signal.last_action == "unknown"

    def test_update_memory_with_empty_data(self, memory_handler, forge_result_with_empty_data):
        """
        Test updating memory with empty data dict.
        """
        memory_handler.update_memory(forge_result_with_empty_data)
        
        assert "unknown" in memory_handler.memory_signal.recent_assets

    def test_update_memory_multiple_times_increments_query_count(self, memory_handler, coingecko_forge_result):
        """
        Test that query count increments with multiple updates.
        """
        memory_handler.update_memory(coingecko_forge_result)
        assert memory_handler.memory_signal.query_count_1h == 1
        
        memory_handler.update_memory(github_forge_result)
        assert memory_handler.memory_signal.query_count_1h == 2
        
        memory_handler.update_memory(weather_forge_result)
        assert memory_handler.memory_signal.query_count_1h == 3

    def test_update_memory_maintains_max_5_recent_services(self, memory_handler):
        """
        Test that recent services list maintains max 5 entries.
        """
        # Add 7 different services
        for i in range(7):
            result = ForgeResult(
                success=True,
                service=f"service_{i}",
                data={},
                ascii_visual=None,
                error=None
            )
            memory_handler.update_memory(result)
        
        # Should only have last 5
        assert len(memory_handler.memory_signal.recent_services) == 5
        assert "service_0" not in memory_handler.memory_signal.recent_services
        assert "service_1" not in memory_handler.memory_signal.recent_services
        assert "service_5" in memory_handler.memory_signal.recent_services
        assert "service_6" in memory_handler.memory_signal.recent_services

    def test_update_memory_maintains_max_5_recent_assets(self, memory_handler):
        """
        Test that recent assets list maintains max 5 entries.
        """
        # Add 7 different assets
        for i in range(7):
            result = ForgeResult(
                success=True,
                service="coingecko",
                data={f"ASSET_{i}": {"price": i * 100}},
                ascii_visual=None,
                error=None
            )
            memory_handler.update_memory(result)
        
        # Should only have last 5
        assert len(memory_handler.memory_signal.recent_assets) == 5
        assert "ASSET_0" not in memory_handler.memory_signal.recent_assets
        assert "ASSET_1" not in memory_handler.memory_signal.recent_assets
        assert "ASSET_5" in memory_handler.memory_signal.recent_assets
        assert "ASSET_6" in memory_handler.memory_signal.recent_assets

    def test_update_memory_with_trend_data_only(self, memory_handler):
        """
        Test updating memory when data only contains trend_data.
        """
        result = ForgeResult(
            success=True,
            service="coingecko",
            data={"trend_data": [1, 2, 3]},
            ascii_visual=None,
            error=None
        )
        memory_handler.update_memory(result)
        
        # Should default to "unknown" asset
        assert "unknown" in memory_handler.memory_signal.recent_assets

    def test_update_memory_preserves_order_of_recent_services(self, memory_handler):
        """
        Test that recent services maintains insertion order.
        """
        services = ["service_a", "service_b", "service_c"]
        for service in services:
            result = ForgeResult(
                success=True,
                service=service,
                data={},
                ascii_visual=None,
                error=None
            )
            memory_handler.update_memory(result)
        
        assert memory_handler.memory_signal.recent_services == services

    def test_update_memory_with_duplicate_service(self, memory_handler):
        """
        Test updating memory with same service multiple times.
        """
        result = ForgeResult(
            success=True,
            service="coingecko",
            data={"BTC": {"price": 50000}},
            ascii_visual=None,
            error=None
        )
        
        memory_handler.update_memory(result)
        memory_handler.update_memory(result)
        memory_handler.update_memory(result)
        
        # All three should be in recent services
        assert memory_handler.memory_signal.recent_services.count("coingecko") == 3


# =============================================================================
# Test: Get Recent Services
# =============================================================================

class TestGetRecentServices:
    """Test cases for the get_recent_services method."""

    def test_get_recent_services_empty(self, memory_handler):
        """
        Test getting recent services when list is empty.
        """
        services = memory_handler.get_recent_services()
        assert services == []

    def test_get_recent_services_with_data(self, memory_handler):
        """
        Test getting recent services with data present.
        """
        result = ForgeResult(
            success=True,
            service="coingecko",
            data={},
            ascii_visual=None,
            error=None
        )
        memory_handler.update_memory(result)
        
        services = memory_handler.get_recent_services()
        assert services == ["coingecko"]

    def test_get_recent_services_returns_copy(self, memory_handler):
        """
        Test that get_recent_services returns a copy, not reference.
        """
        result = ForgeResult(
            success=True,
            service="coingecko",
            data={},
            ascii_visual=None,
            error=None
        )
        memory_handler.update_memory(result)
        
        services = memory_handler.get_recent_services()
        services.append("new_service")
        
        # Original should not be modified
        assert "new_service" not in memory_handler.memory_signal.recent_services

    def test_get_recent_services_with_multiple_entries(self, memory_handler):
        """
        Test getting recent services with multiple entries.
        """
        services = ["service_a", "service_b", "service_c"]
        for service in services:
            result = ForgeResult(
                success=True,
                service=service,
                data={},
                ascii_visual=None,
                error=None
            )
            memory_handler.update_memory(result)
        
        retrieved = memory_handler.get_recent_services()
        assert retrieved == services


# =============================================================================
# Test: Get Recent Assets
# =============================================================================

class TestGetRecentAssets:
    """Test cases for the get_recent_assets method."""

    def test_get_recent_assets_empty(self, memory_handler):
        """
        Test getting recent assets when list is empty.
        """
        assets = memory_handler.get_recent_assets()
        assert assets == []

    def test_get_recent_assets_with_data(self, memory_handler):
        """
        Test getting recent assets with data present.
        """
        result = ForgeResult(
            success=True,
            service="coingecko",
            data={"BTC": {"price": 50000}},
            ascii_visual=None,
            error=None
        )
        memory_handler.update_memory(result)
        
        assets = memory_handler.get_recent_assets()
        assert assets == ["BTC"]

    def test_get_recent_assets_returns_copy(self, memory_handler):
        """
        Test that get_recent_assets returns a copy, not reference.
        """
        result = ForgeResult(
            success=True,
            service="coingecko",
            data={"BTC": {"price": 50000}},
            ascii_visual=None,
            error=None
        )
        memory_handler.update_memory(result)
        
        assets = memory_handler.get_recent_assets()
        assets.append("new_asset")
        
        # Original should not be modified
        assert "new_asset" not in memory_handler.memory_signal.recent_assets

    def test_get_recent_assets_with_multiple_entries(self, memory_handler):
        """
        Test getting recent assets with multiple entries.
        """
        assets = ["BTC", "ETH", "SOL"]
        for asset in assets:
            result = ForgeResult(
                success=True,
                service="coingecko",
                data={asset: {"price": 50000}},
                ascii_visual=None,
                error=None
            )
            memory_handler.update_memory(result)
        
        retrieved = memory_handler.get_recent_assets()
        assert retrieved == assets


# =============================================================================
# Test: Get Last Action
# =============================================================================

class TestGetLastAction:
    """Test cases for the get_last_action method."""

    def test_get_last_action_when_none(self, memory_handler):
        """
        Test getting last action when it's None.
        """
        action = memory_handler.get_last_action()
        assert action is None

    def test_get_last_action_with_data(self, memory_handler):
        """
        Test getting last action after update.
        """
        result = ForgeResult(
            success=True,
            service="coingecko",
            data={},
            ascii_visual=None,
            error=None
        )
        memory_handler.update_memory(result)
        
        action = memory_handler.get_last_action()
        assert action == "coingecko"

    def test_get_last_action_updates_on_new_update(self, memory_handler):
        """
        Test that last action updates with each new update.
        """
        result1 = ForgeResult(
            success=True,
            service="coingecko",
            data={},
            ascii_visual=None,
            error=None
        )
        result2 = ForgeResult(
            success=True,
            service="github",
            data={},
            ascii_visual=None,
            error=None
        )
        
        memory_handler.update_memory(result1)
        assert memory_handler.get_last_action() == "coingecko"
        
        memory_handler.update_memory(result2)
        assert memory_handler.get_last_action() == "github"


# =============================================================================
# Test: Get Query Count
# =============================================================================

class TestGetQueryCount:
    """Test cases for the get_query_count method."""

    def test_get_query_count_initial_value(self, memory_handler):
        """
        Test getting query count with initial value.
        """
        count = memory_handler.get_query_count()
        assert count == 0

    def test_get_query_count_after_updates(self, memory_handler):
        """
        Test getting query count after multiple updates.
        """
        for i in range(5):
            result = ForgeResult(
                success=True,
                service=f"service_{i}",
                data={},
                ascii_visual=None,
                error=None
            )
            memory_handler.update_memory(result)
        
        count = memory_handler.get_query_count()
        assert count == 5

    def test_get_query_count_increments_correctly(self, memory_handler):
        """
        Test that query count increments by 1 each update.
        """
        result = ForgeResult(
            success=True,
            service="coingecko",
            data={},
            ascii_visual=None,
            error=None
        )
        
        initial_count = memory_handler.get_query_count()
        memory_handler.update_memory(result)
        new_count = memory_handler.get_query_count()
        
        assert new_count == initial_count + 1


# =============================================================================
# Test: Reset Query Count
# =============================================================================

class TestResetQueryCount:
    """Test cases for the reset_query_count method."""

    def test_reset_query_count_from_zero(self, memory_handler):
        """
        Test resetting query count when it's already zero.
        """
        memory_handler.reset_query_count()
        assert memory_handler.get_query_count() == 0

    def test_reset_query_count_from_nonzero(self, memory_handler):
        """
        Test resetting query count from non-zero value.
        """
        result = ForgeResult(
            success=True,
            service="coingecko",
            data={},
            ascii_visual=None,
            error=None
        )
        memory_handler.update_memory(result)
        memory_handler.update_memory(result)
        
        assert memory_handler.get_query_count() == 2
        memory_handler.reset_query_count()
        assert memory_handler.get_query_count() == 0

    def test_reset_query_count_multiple_times(self, memory_handler):
        """
        Test that reset can be called multiple times.
        """
        result = ForgeResult(
            success=True,
            service="coingecko",
            data={},
            ascii_visual=None,
            error=None
        )
        memory_handler.update_memory(result)
        
        memory_handler.reset_query_count()
        memory_handler.reset_query_count()
        memory_handler.reset_query_count()
        
        assert memory_handler.get_query_count() == 0


# =============================================================================
# Test: Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test cases for edge cases and boundary conditions."""

    def test_update_memory_with_none_result(self, memory_handler):
        """
        Test that updating with None result doesn't crash.
        """
        # This would normally fail, but we test the behavior
        with pytest.raises(AttributeError):
            memory_handler.update_memory(None)

    def test_update_memory_with_coingecko_multiple_assets(self, memory_handler):
        """
        Test updating memory when CoinGecko returns multiple assets.
        """
        result = ForgeResult(
            success=True,
            service="coingecko",
            data={"BTC": {"price": 50000}, "ETH": {"price": 3000}, "trend_data": []},
            ascii_visual=None,
            error=None
        )
        memory_handler.update_memory(result)
        
        # Should pick the first non-trend_data key
        assert "BTC" in memory_handler.memory_signal.recent_assets

    def test_get_recent_services_returns_list_not_deque(self, memory_handler):
        """
        Test that get_recent_services returns a list type.
        """
        result = ForgeResult(
            success=True,
            service="coingecko",
            data={},
            ascii_visual=None,
            error=None
        )
        memory_handler.update_memory(result)
        
        services = memory_handler.get_recent_services()
        assert isinstance(services, list)

    def test_get_recent_assets_returns_list_not_deque(self, memory_handler):
        """
        Test that get_recent_assets returns a list type.
        """
        result = ForgeResult(
            success=True,
            service="coingecko",
            data={"BTC": {"price": 50000}},
            ascii_visual=None,
            error=None
        )
        memory_handler.update_memory(result)
        
        assets = memory_handler.get_recent_assets()
        assert isinstance(assets, list)

    def test_get_last_action_returns_string(self, memory_handler):
        """
        Test that get_last_action returns a string type when set.
        """
        result = ForgeResult(
            success=True,
            service="coingecko",
            data={},
            ascii_visual=None,
            error=None
        )
        memory_handler.update_memory(result)
        
        action = memory_handler.get_last_action()
        assert isinstance(action, str)

    def test_get_query_count_returns_int(self, memory_handler):
        """
        Test that get_query_count returns an integer.
        """
        count = memory_handler.get_query_count()
        assert isinstance(count, int)
