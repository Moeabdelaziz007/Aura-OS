import pytest
import asyncio
import os
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from agent.aether_forge.aether_forge import AetherForge
from agent.aether_forge.models import ForgeResult, CognitiveSystem
from agent.aether_forge.compiler import CompiledAgent

@pytest.fixture
def mock_httpx():
    with patch('httpx.AsyncClient') as mock:
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.__aexit__.return_value = None
        mock.return_value = client
        yield client

@pytest.fixture
def forge(mock_httpx):
    # Patch dependencies to avoid side effects
    with patch('agent.aether_forge.aether_forge.AetherNexus', MagicMock()), \
         patch('agent.aether_forge.aether_forge.AetherCloudNexus', MagicMock()), \
         patch('agent.aether_forge.aether_forge.AetherConstraintSolver', MagicMock()), \
         patch('agent.aether_forge.aether_forge.AetherAgentParliament') as MockParliament, \
         patch('agent.aether_forge.aether_forge.AetherTemporalMemoryTides', MagicMock()), \
         patch('agent.aether_forge.aether_forge.AetherNanoAgentCompiler') as MockCompiler, \
         patch('agent.aether_forge.aether_forge.AetherNanoSandbox') as MockSandbox, \
         patch('agent.aether_forge.aether_forge.ForgeMetrics.record', Mock()), \
         patch('asyncio.create_task', Mock()): # Prevent tide daemon task

        # Setup mocks
        MockParliament.return_value.aether_deliberate = AsyncMock()
        MockCompiler.return_value.compile_variants = AsyncMock()
        MockSandbox.return_value.execute = AsyncMock()

        forge = AetherForge(automated_tides=False)
        # Manually set client to mock
        forge.client = mock_httpx
        yield forge

@pytest.mark.asyncio
async def test_forge_and_deploy_coingecko(forge):
    # mock httpx, verify 4-phase protocol runs
    # Coingecko is a static executor

    intent_data = {
        "service": "coingecko",
        "params": {"coins": ["bitcoin"], "currencies": ["usd"]}
    }

    # Mock circuit breaker to just run the function
    async def mock_call(service, func, *args, **kwargs):
        return await func(*args, **kwargs)

    with patch.object(forge.circuit, 'call', side_effect=mock_call):
        # Create a mock executor
        mock_executor = AsyncMock()
        mock_executor.execute = AsyncMock(return_value={"bitcoin": {"usd": 50000}})

        # We need to register it
        mock_executor_cls = Mock(return_value=mock_executor)
        forge.REGISTRY["coingecko"] = mock_executor_cls

        # We also need to mock parliament deliberate
        forge.parliament.aether_deliberate.return_value = MagicMock()

        result = await forge.aether_forge_and_deploy(intent_data)

        assert result.success is True
        assert result.service == "coingecko"
        # The executor's return value is used as data
        assert result.data == {"bitcoin": {"usd": 50000}}
        assert result.cognitive_system == CognitiveSystem.SYSTEM_1

@pytest.mark.asyncio
async def test_forge_and_deploy_invalid_service(forge):
    # returns error gracefully
    # If service is unknown and dynamic compilation fails

    intent_data = {
        "service": "unknown_service",
        "query": "do something weird"
    }

    # Mock dynamic compilation to fail or return empty
    forge.compiler.compile_variants.return_value = []

    # Mock parliament deliberate
    forge.parliament.aether_deliberate.return_value = MagicMock()

    result = await forge.aether_forge_and_deploy(intent_data)

    assert result.success is False
    assert result.service == "unknown_service"
    # Depending on implementation, it might say "Swarm Compilation Failed" or "Compiler error"
    assert "Failed" in result.error or "error" in result.error.lower()

@pytest.mark.asyncio
async def test_nano_agent_lifecycle(forge):
    # spawn → hydrate → execute → dehydrate → dissolve
    # This corresponds to dynamic execution

    intent_data = {
        "service": "dynamic_calc",
        "query": "calculate 2+2"
    }

    # Mock compiler to return a valid agent
    # Using correct signature for CompiledAgent
    real_agent = CompiledAgent(code="result={'val': 4}")
    forge.compiler.compile_variants.return_value = [real_agent]

    # Mock sandbox execution
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.data = {"val": 4}
    mock_result.error = None
    forge.sandbox.execute.return_value = mock_result

    # Mock parliament deliberate
    forge.parliament.aether_deliberate.return_value = MagicMock()

    result = await forge.aether_forge_and_deploy(intent_data)

    assert result.success is True
    assert result.service == "dynamic_calc"
    assert result.cognitive_system == CognitiveSystem.SYSTEM_2
    assert result.data == {"val": 4}

def test_cloud_nexus_initialization_no_hardcoded_id():
    """Verify that AetherForge does not use a hardcoded Project ID if env var is missing."""
    with patch.dict(os.environ, {}, clear=True), \
         patch('agent.aether_forge.aether_forge.AetherCloudNexus') as MockCloudNexus, \
         patch('agent.aether_forge.aether_forge.AetherNexus'), \
         patch('agent.aether_forge.aether_forge.httpx.AsyncClient'), \
         patch('agent.aether_forge.aether_forge.AetherAgentParliament'), \
         patch('agent.aether_forge.aether_forge.AetherTemporalMemoryTides'), \
         patch('agent.aether_forge.aether_forge.ForgeMetrics'), \
         patch('agent.aether_forge.aether_forge.AetherMicroVisualizer'), \
         patch('agent.aether_forge.aether_forge.AetherConstraintSolver'), \
         patch('agent.aether_forge.aether_forge.get_circuit_breaker'), \
         patch('agent.aether_forge.aether_forge.AetherNanoAgentCompiler'), \
         patch('agent.aether_forge.aether_forge.AetherNanoSandbox'):

        # We need os.path.exists to return True for the key file check
        # But os.path.exists is also used by other things.
        # We can target the specific call or just let it proceed if key file actually exists.
        # But we cleared env vars, so key path defaults to .idx/aether-key.json.
        # That file exists in repo. So os.path.exists should return True.
        # But if we want to be robust against file system:
        with patch('os.path.exists', return_value=True):
             AetherForge(automated_tides=False)

        if MockCloudNexus.called:
            args, _ = MockCloudNexus.call_args
            # args[0] is project_id
            assert args[0] is None, f"Project ID should be None, got {args[0]}"
        else:
            pytest.fail("AetherCloudNexus was not initialized (likely key file check failed)")
