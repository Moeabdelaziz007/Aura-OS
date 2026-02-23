"""
Unit Tests for API Client Module

Tests the API client operations and integrations for the AetherOS orchestrator.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch


# =============================================================================
# Import the module under test
# =============================================================================

from agent.orchestrator.modules.api_client import APIClient


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def mock_bridge():
    """
    Create a mock AetherNavigator bridge instance.
    """
    bridge = Mock()
    return bridge


@pytest.fixture
def api_client(mock_bridge, mock_api_key):
    """
    Create an APIClient instance with mocked dependencies.
    """
    return APIClient(bridge=mock_bridge, api_key=mock_api_key)


@pytest.fixture
def api_client_custom_key(mock_bridge):
    """
    Create an APIClient instance with custom API key.
    """
    return APIClient(bridge=mock_bridge, api_key="custom-api-key")


@pytest.fixture
def mock_gemini_client_class():
    """
    Mock the GeminiLiveClient class.
    """
    with patch('agent.orchestrator.gemini_live_client.GeminiLiveClient') as mock_class:
        yield mock_class


# =============================================================================
# Test: APIClient Initialization
# =============================================================================

class TestAPIClientInitialization:
    """Test cases for APIClient initialization."""

    def test_initialization_with_defaults(self, mock_bridge, mock_api_key):
        """
        Test that APIClient initializes correctly with default values.
        """
        client = APIClient(mock_bridge, mock_api_key)
        
        assert client.bridge == mock_bridge
        assert client.api_key == mock_api_key
        assert client._gemini_client is None

    def test_initialization_with_custom_api_key(self, mock_bridge):
        """
        Test that APIClient initializes with custom API key.
        """
        custom_key = "my-custom-api-key"
        client = APIClient(mock_bridge, custom_key)
        
        assert client.api_key == custom_key

    def test_initialization_with_none_bridge(self, mock_api_key):
        """
        Test APIClient with None bridge.
        """
        client = APIClient(None, mock_api_key)
        assert client.bridge is None

    def test_initialization_with_empty_api_key(self, mock_bridge):
        """
        Test APIClient with empty API key.
        """
        client = APIClient(mock_bridge, "")
        assert client.api_key == ""

    def test_initialization_client_is_none(self, mock_bridge, mock_api_key):
        """
        Test that _gemini_client is initialized to None.
        """
        client = APIClient(mock_bridge, mock_api_key)
        assert client._gemini_client is None


# =============================================================================
# Test: Create Gemini Client
# =============================================================================

class TestCreateGeminiClient:
    """Test cases for the create_gemini_client method."""

    def test_create_gemini_client_success(self, api_client, mock_gemini_client_class):
        """
        Test successful creation of Gemini Live client.
        """
        mock_instance = Mock()
        mock_gemini_client_class.return_value = mock_instance
        
        client = api_client.create_gemini_client()
        
        # Verify GeminiLiveClient was instantiated correctly
        mock_gemini_client_class.assert_called_once_with(
            api_client.bridge, api_client.api_key
        )
        
        # Verify the instance is stored
        assert api_client._gemini_client == mock_instance
        
        # Verify the instance is returned
        assert client == mock_instance

    def test_create_gemini_client_stores_reference(self, api_client, mock_gemini_client_class):
        """
        Test that created client is stored in _gemini_client.
        """
        mock_instance = Mock()
        mock_gemini_client_class.return_value = mock_instance
        
        api_client.create_gemini_client()
        
        assert api_client._gemini_client is not None
        assert api_client._gemini_client == mock_instance

    def test_create_gemini_client_multiple_times(self, api_client, mock_gemini_client_class):
        """
        Test creating Gemini client multiple times (should replace previous).
        """
        mock_instance1 = Mock()
        mock_instance2 = Mock()
        mock_gemini_client_class.side_effect = [mock_instance1, mock_instance2]
        
        client1 = api_client.create_gemini_client()
        assert api_client._gemini_client == mock_instance1
        
        client2 = api_client.create_gemini_client()
        assert api_client._gemini_client == mock_instance2
        assert api_client._gemini_client != mock_instance1

    def test_create_gemini_client_with_special_characters_in_key(self, mock_bridge, mock_gemini_client_class):
        """
        Test creating client with special characters in API key.
        """
        special_key = "key-with-special_chars!@#$%^&*()"
        client = APIClient(mock_bridge, special_key)
        
        mock_instance = Mock()
        mock_gemini_client_class.return_value = mock_instance
        
        client.create_gemini_client()
        
        mock_gemini_client_class.assert_called_once_with(mock_bridge, special_key)


# =============================================================================
# Test: Connect Gemini Client
# =============================================================================

class TestConnectGeminiClient:
    """Test cases for the connect_gemini_client method."""

    @pytest.mark.asyncio
    async def test_connect_gemini_client_success(self, api_client):
        """
        Test successful connection of Gemini Live client.
        """
        mock_client = Mock()
        mock_client.connect = AsyncMock()
        
        await api_client.connect_gemini_client(mock_client)
        
        mock_client.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_gemini_client_creates_background_task(self, api_client):
        """
        Test that connect creates a background task.
        """
        mock_client = Mock()
        mock_client.connect = AsyncMock()
        
        # This should create a background task
        await api_client.connect_gemini_client(mock_client)
        
        # Verify connect was called
        mock_client.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_gemini_client_with_connection_error(self, api_client):
        """
        Test handling connection error gracefully.
        """
        mock_client = Mock()
        mock_client.connect = AsyncMock(side_effect=ConnectionError("Connection failed"))
        
        # Should not raise exception (creates background task)
        await api_client.connect_gemini_client(mock_client)
        
        # The error would occur in the background task
        assert True

    @pytest.mark.asyncio
    async def test_connect_gemini_client_with_timeout(self, api_client):
        """
        Test handling connection timeout gracefully.
        """
        mock_client = Mock()
        mock_client.connect = AsyncMock(side_effect=asyncio.TimeoutError("Connection timeout"))
        
        # Should not raise exception (creates background task)
        await api_client.connect_gemini_client(mock_client)
        
        assert True


# =============================================================================
# Test: Close Gemini Client
# =============================================================================

class TestCloseGeminiClient:
    """Test cases for the close_gemini_client method."""

    @pytest.mark.asyncio
    async def test_close_gemini_client_success(self, api_client):
        """
        Test successful closing of Gemini Live client.
        """
        mock_client = Mock()
        mock_client.close = AsyncMock()
        
        await api_client.close_gemini_client(mock_client)
        
        mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_gemini_client_with_error(self, api_client):
        """
        Test handling close error gracefully.
        """
        mock_client = Mock()
        mock_client.close = AsyncMock(side_effect=Exception("Close failed"))
        
        # Should raise exception
        with pytest.raises(Exception, match="Close failed"):
            await api_client.close_gemini_client(mock_client)

    @pytest.mark.asyncio
    async def test_close_gemini_client_multiple_times(self, api_client):
        """
        Test closing the same client multiple times.
        """
        mock_client = Mock()
        mock_client.close = AsyncMock()
        
        await api_client.close_gemini_client(mock_client)
        await api_client.close_gemini_client(mock_client)
        await api_client.close_gemini_client(mock_client)
        
        assert mock_client.close.call_count == 3

    @pytest.mark.asyncio
    async def test_close_gemini_client_none_client(self, api_client):
        """
        Test closing None client.
        """
        # Should raise AttributeError
        with pytest.raises(AttributeError):
            await api_client.close_gemini_client(None)


# =============================================================================
# Test: Get Current Client
# =============================================================================

class TestGetCurrentClient:
    """Test cases for the get_current_client method."""

    def test_get_current_client_when_none(self, api_client):
        """
        Test getting current client when none exists.
        """
        client = api_client.get_current_client()
        assert client is None

    def test_get_current_client_after_creation(self, api_client, mock_gemini_client_class):
        """
        Test getting current client after creation.
        """
        mock_instance = Mock()
        mock_gemini_client_class.return_value = mock_instance
        
        api_client.create_gemini_client()
        
        client = api_client.get_current_client()
        assert client == mock_instance

    def test_get_current_client_returns_reference(self, api_client, mock_gemini_client_class):
        """
        Test that get_current_client returns the actual reference.
        """
        mock_instance = Mock()
        mock_gemini_client_class.return_value = mock_instance
        
        api_client.create_gemini_client()
        
        client1 = api_client.get_current_client()
        client2 = api_client.get_current_client()
        
        # Should be the same object
        assert client1 is client2

    def test_get_current_client_after_replacement(self, api_client, mock_gemini_client_class):
        """
        Test getting current client after replacement.
        """
        mock_instance1 = Mock()
        mock_instance2 = Mock()
        mock_gemini_client_class.side_effect = [mock_instance1, mock_instance2]
        
        api_client.create_gemini_client()
        assert api_client.get_current_client() == mock_instance1
        
        api_client.create_gemini_client()
        assert api_client.get_current_client() == mock_instance2


# =============================================================================
# Test: Set API Key
# =============================================================================

class TestSetAPIKey:
    """Test cases for the set_api_key method."""

    def test_set_api_key_success(self, api_client):
        """
        Test successful API key update.
        """
        new_key = "new-api-key-123"
        api_client.set_api_key(new_key)
        
        assert api_client.api_key == new_key

    def test_set_api_key_multiple_times(self, api_client):
        """
        Test setting API key multiple times.
        """
        keys = ["key1", "key2", "key3"]
        
        for key in keys:
            api_client.set_api_key(key)
            assert api_client.api_key == key

    def test_set_api_key_empty_string(self, api_client):
        """
        Test setting API key to empty string.
        """
        api_client.set_api_key("")
        assert api_client.api_key == ""

    def test_set_api_key_with_special_characters(self, api_client):
        """
        Test setting API key with special characters.
        """
        special_key = "key!@#$%^&*()_+-=[]{}|;':\",./<>?"
        api_client.set_api_key(special_key)
        
        assert api_client.api_key == special_key

    def test_set_api_key_with_unicode(self, api_client):
        """
        Test setting API key with unicode characters.
        """
        unicode_key = "key-🔑-مفتاح"
        api_client.set_api_key(unicode_key)
        
        assert api_client.api_key == unicode_key

    def test_set_api_key_very_long(self, api_client):
        """
        Test setting very long API key.
        """
        long_key = "x" * 10000
        api_client.set_api_key(long_key)
        
        assert api_client.api_key == long_key
        assert len(api_client.api_key) == 10000


# =============================================================================
# Test: Get API Key
# =============================================================================

class TestGetAPIKey:
    """Test cases for the get_api_key method."""

    def test_get_api_key_initial_value(self, api_client, mock_api_key):
        """
        Test getting initial API key value.
        """
        key = api_client.get_api_key()
        assert key == mock_api_key

    def test_get_api_key_after_update(self, api_client):
        """
        Test getting API key after update.
        """
        new_key = "updated-key"
        api_client.set_api_key(new_key)
        
        key = api_client.get_api_key()
        assert key == new_key

    def test_get_api_key_returns_string(self, api_client):
        """
        Test that get_api_key returns a string.
        """
        key = api_client.get_api_key()
        assert isinstance(key, str)

    def test_get_api_key_multiple_calls(self, api_client, mock_api_key):
        """
        Test that multiple calls return the same value.
        """
        key1 = api_client.get_api_key()
        key2 = api_client.get_api_key()
        key3 = api_client.get_api_key()
        
        assert key1 == key2 == key3 == mock_api_key


# =============================================================================
# Test: Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test cases for edge cases and boundary conditions."""

    def test_api_client_with_none_api_key(self, mock_bridge):
        """
        Test APIClient with None API key.
        """
        client = APIClient(mock_bridge, None)
        assert client.api_key is None

    def test_create_client_with_none_api_key(self, mock_bridge, mock_gemini_client_class):
        """
        Test creating client when API key is None.
        """
        client = APIClient(mock_bridge, None)
        mock_instance = Mock()
        mock_gemini_client_class.return_value = mock_instance
        
        client.create_gemini_client()
        
        mock_gemini_client_class.assert_called_once_with(mock_bridge, None)

    def test_set_api_key_to_none(self, api_client):
        """
        Test setting API key to None.
        """
        api_client.set_api_key(None)
        assert api_client.api_key is None

    def test_api_client_with_whitespace_key(self, mock_bridge):
        """
        Test APIClient with whitespace-only API key.
        """
        client = APIClient(mock_bridge, "   ")
        assert client.api_key == "   "

    def test_set_api_key_whitespace(self, api_client):
        """
        Test setting API key to whitespace.
        """
        api_client.set_api_key("   \t\n  ")
        assert api_client.api_key == "   \t\n  "

    @pytest.mark.asyncio
    async def test_connect_client_with_none_client(self, api_client):
        """
        Test connecting None client.
        """
        # Should raise AttributeError
        with pytest.raises(AttributeError):
            await api_client.connect_gemini_client(None)

    def test_get_current_client_does_not_modify_internal_state(self, api_client, mock_gemini_client_class):
        """
        Test that get_current_client doesn't modify internal state.
        """
        mock_instance = Mock()
        mock_gemini_client_class.return_value = mock_instance
        
        api_client.create_gemini_client()
        
        # Get client multiple times
        for _ in range(10):
            api_client.get_current_client()
        
        # Internal reference should remain the same
        assert api_client._gemini_client == mock_instance

    def test_create_client_with_different_bridge(self, mock_gemini_client_class):
        """
        Test creating client with different bridge instances.
        """
        bridge1 = Mock()
        bridge2 = Mock()
        
        client1 = APIClient(bridge1, "key1")
        client2 = APIClient(bridge2, "key2")
        
        mock_instance1 = Mock()
        mock_instance2 = Mock()
        mock_gemini_client_class.side_effect = [mock_instance1, mock_instance2]
        
        created1 = client1.create_gemini_client()
        created2 = client2.create_gemini_client()
        
        assert created1 == mock_instance1
        assert created2 == mock_instance2
        assert created1 != created2
