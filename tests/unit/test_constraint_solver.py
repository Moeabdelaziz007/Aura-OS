"""
Unit Tests for Constraint Solver Module

Tests the constraint solving logic including empty list fixes.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


# =============================================================================
# Import the module under test
# =============================================================================

from agent.aether_forge.constraint_solver import (
    AetherConstraintSolver as ConstraintSolver,
    IntentTemplate,
    MemorySignal,
    compute_tau,
    classify_urgency,
    extract_asset,
    INTENT_CATALOG,
    ASSET_PATTERNS,
    build_time_context,
    TAU_MIN,
    TAU_MAX
)
from agent.aether_forge.models import (
    VoiceFeatures,
    ScreenContext,
    TimeContext,
    UrgencyLevel,
    CognitiveSystem
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def constraint_solver():
    """
    Create a ConstraintSolver instance.
    """
    return ConstraintSolver()


@pytest.fixture
def mock_voice_features():
    """
    Create a mock VoiceFeatures instance.
    """
    return VoiceFeatures(
        speech_rate_wpm=150.0,
        pitch_variance=0.5,
        volume_db=60.0,
        pause_frequency=10.0,
        transcript="check bitcoin price",
        language="en"
    )


@pytest.fixture
def mock_screen_context():
    """
    Create a mock ScreenContext instance.
    """
    return ScreenContext(
        raw_description="Binance trading interface",
        detected_assets=["BTC", "SOL"],
        detected_app="Binance",
        detected_numbers=[50000.0, 2500.0],
        confidence=0.9
    )


@pytest.fixture
def mock_time_context():
    """
    Create a mock TimeContext instance.
    """
    return TimeContext(
        hour=14,
        is_market_hours=True,
        day_of_week=1,
        is_weekend=False,
        market_session="open"
    )


@pytest.fixture
def mock_memory_signal():
    """
    Create a mock MemorySignal instance.
    """
    return MemorySignal(
        recent_services=["coingecko", "github"],
        recent_assets=["BTC", "ETH"],
        last_action="coingecko",
        query_count_1h=5
    )


# =============================================================================
# Test: Compute Tau Function
# =============================================================================

class TestComputeTau:
    """Test cases for the compute_tau function."""

    def test_compute_tau_high_urgency(self):
        """
        Test tau calculation with high urgency (0.9).
        """
        tau, system = compute_tau(0.9)
        
        # High urgency → low tau → System 1
        assert tau < 0.5
        assert tau >= TAU_MIN
        assert system == CognitiveSystem.SYSTEM_1

    def test_compute_tau_low_urgency(self):
        """
        Test tau calculation with low urgency (0.1).
        """
        tau, system = compute_tau(0.1)
        
        # Low urgency → high tau → System 2
        assert tau > 0.5
        assert tau <= TAU_MAX
        assert system == CognitiveSystem.SYSTEM_2

    def test_compute_tau_medium_urgency(self):
        """
        Test tau calculation with medium urgency (0.5).
        """
        tau, system = compute_tau(0.5)
        
        # Medium urgency → tau around 0.5
        assert 0.45 <= tau <= 0.55

    def test_compute_tau_urgency_zero(self):
        """
        Test tau calculation with urgency of 0.0.
        """
        tau, system = compute_tau(0.0)
        
        assert tau == pytest.approx(TAU_MAX, rel=1e-6)
        assert system == CognitiveSystem.SYSTEM_2

    def test_compute_tau_urgency_one(self):
        """
        Test tau calculation with urgency of 1.0.
        """
        tau, system = compute_tau(1.0)
        
        assert tau == pytest.approx(TAU_MIN, rel=1e-6)
        assert system == CognitiveSystem.SYSTEM_1

    def test_compute_tau_returns_rounded_value(self):
        """
        Test that tau is rounded to 3 decimal places.
        """
        tau, _ = compute_tau(0.5)
        
        # Check that tau has at most 3 decimal places
        assert tau == round(tau, 3)


# =============================================================================
# Test: Classify Urgency Function
# =============================================================================

class TestClassifyUrgency:
    """Test cases for the classify_urgency function."""

    def test_classify_urgency_critical(self):
        """
        Test urgency classification for critical level.
        """
        for score in [0.85, 0.9, 0.95, 1.0]:
            level = classify_urgency(score)
            assert level == UrgencyLevel.CRITICAL

    def test_classify_urgency_high(self):
        """
        Test urgency classification for high level.
        """
        for score in [0.65, 0.7, 0.75, 0.84]:
            level = classify_urgency(score)
            assert level == UrgencyLevel.HIGH

    def test_classify_urgency_medium(self):
        """
        Test urgency classification for medium level.
        """
        for score in [0.45, 0.5, 0.55, 0.64]:
            level = classify_urgency(score)
            assert level == UrgencyLevel.MEDIUM

    def test_classify_urgency_low(self):
        """
        Test urgency classification for low level.
        """
        for score in [0.25, 0.3, 0.35, 0.44]:
            level = classify_urgency(score)
            assert level == UrgencyLevel.LOW

    def test_classify_urgency_minimal(self):
        """
        Test urgency classification for minimal level.
        """
        for score in [0.0, 0.1, 0.15, 0.24]:
            level = classify_urgency(score)
            assert level == UrgencyLevel.MINIMAL

    def test_classify_urgency_boundary_values(self):
        """
        Test urgency classification at boundary values.
        """
        assert classify_urgency(0.85) == UrgencyLevel.CRITICAL
        assert classify_urgency(0.65) == UrgencyLevel.HIGH
        assert classify_urgency(0.45) == UrgencyLevel.MEDIUM
        assert classify_urgency(0.25) == UrgencyLevel.LOW


# =============================================================================
# Test: Extract Asset Function
# =============================================================================

class TestExtractAsset:
    """Test cases for the extract_asset function."""

    def test_extract_asset_from_query_bitcoin(self):
        """
        Test extracting bitcoin asset from query.
        """
        queries = ["bitcoin price", "check btc", "how much is BTC", "بيتكوين"]
        
        for query in queries:
            asset = extract_asset(query)
            assert asset == "bitcoin"

    def test_extract_asset_from_query_solana(self):
        """
        Test extracting solana asset from query.
        """
        queries = ["solana price", "check sol", "how much is SOL", "سولانا"]
        
        for query in queries:
            asset = extract_asset(query)
            assert asset == "solana"

    def test_extract_asset_from_query_ethereum(self):
        """
        Test extracting ethereum asset from query.
        """
        queries = ["ethereum price", "check eth", "how much is ETH", "إيث"]
        
        for query in queries:
            asset = extract_asset(query)
            assert asset == "ethereum"

    def test_extract_asset_from_query_cairo(self):
        """
        Test extracting cairo asset from query.
        """
        queries = ["weather in cairo", "القاهرة طقس", "cairo temperature"]
        
        for query in queries:
            asset = extract_asset(query)
            assert asset == "cairo"

    def test_extract_asset_from_query_london(self):
        """
        Test extracting london asset from query.
        """
        queries = ["weather in london", "london temperature", "لندن طقس"]
        
        for query in queries:
            asset = extract_asset(query)
            assert asset == "london"

    def test_extract_asset_from_screen_context(self, mock_screen_context):
        """
        Test extracting asset from screen context.
        """
        query = "check price"  # Ambiguous query
        asset = extract_asset(query, mock_screen_context)
        
        # Should extract from screen context
        assert asset in ["bitcoin", "solana"]

    def test_extract_asset_from_detected_app(self):
        """
        Test extracting asset from detected app name.
        """
        screen_ctx = ScreenContext(
            raw_description="Trading interface",
            detected_assets=[],
            detected_app="solana",
            detected_numbers=[],
            confidence=0.8
        )
        
        asset = extract_asset("check price", screen_ctx)
        assert asset == "solana"

    def test_extract_asset_no_match(self):
        """
        Test extracting asset when no match found.
        """
        asset = extract_asset("check something random")
        assert asset is None

    def test_extract_asset_case_insensitive(self):
        """
        Test that asset extraction is case insensitive.
        """
        queries = ["BITCOIN", "Bitcoin", "BiTcOiN"]
        
        for query in queries:
            asset = extract_asset(query)
            assert asset == "bitcoin"

    def test_extract_asset_with_mixed_content(self):
        """
        Test extracting asset from mixed content query.
        """
        query = "What is the price of BTC and SOL today?"
        asset = extract_asset(query)
        
        # Should return first match
        assert asset in ["bitcoin", "solana"]


# =============================================================================
# Test: ConstraintSolver Initialization
# =============================================================================

class TestConstraintSolverInitialization:
    """Test cases for ConstraintSolver initialization."""

    def test_initialization(self):
        """
        Test that ConstraintSolver initializes correctly.
        """
        solver = ConstraintSolver()
        
        assert solver.feedback is not None
        assert solver.CONFIDENCE_THRESHOLD == 0.35


# =============================================================================
# Test: Resolve Method
# =============================================================================

class TestResolve:
    """Test cases for the resolve method."""

    def test_resolve_price_check_query(self, constraint_solver):
        """
        Test resolving a price check query.
        """
        intent = constraint_solver.resolve(
            query="check bitcoin price",
            voice=None,
            screen=None,
            time_ctx=None,
            memory=None
        )
        
        assert intent.action == "price_check"
        assert intent.target in ["bitcoin", "unknown"]
        assert intent.raw_query == "check bitcoin price"

    def test_resolve_github_search_query(self, constraint_solver):
        """
        Test resolving a github search query.
        """
        intent = constraint_solver.resolve(
            query="search github repository",
            voice=None,
            screen=None,
            time_ctx=None,
            memory=None
        )
        
        assert intent.action == "github_search"
        assert intent.raw_query == "search github repository"

    def test_resolve_weather_check_query(self, constraint_solver):
        """
        Test resolving a weather check query.
        """
        intent = constraint_solver.resolve(
            query="what's the weather in cairo",
            voice=None,
            screen=None,
            time_ctx=None,
            memory=None
        )
        
        assert intent.action == "weather_check"
        assert intent.target in ["cairo", "unknown"]

    def test_resolve_with_voice_features(self, constraint_solver, mock_voice_features):
        """
        Test resolving with voice features.
        """
        intent = constraint_solver.resolve(
            query="check price",
            voice=mock_voice_features,
            screen=None,
            time_ctx=None,
            memory=None
        )
        
        # Should incorporate voice urgency
        assert intent.urgency in [
            UrgencyLevel.CRITICAL, UrgencyLevel.HIGH,
            UrgencyLevel.MEDIUM, UrgencyLevel.LOW, UrgencyLevel.MINIMAL
        ]

    def test_resolve_with_screen_context(self, constraint_solver, mock_screen_context):
        """
        Test resolving with screen context.
        """
        intent = constraint_solver.resolve(
            query="check price",
            voice=None,
            screen=mock_screen_context,
            time_ctx=None,
            memory=None
        )
        
        # Should extract asset from screen
        assert intent.target in ["bitcoin", "solana"]

    def test_resolve_with_time_context(self, constraint_solver, mock_time_context):
        """
        Test resolving with time context.
        """
        intent = constraint_solver.resolve(
            query="check price",
            voice=None,
            screen=None,
            time_ctx=mock_time_context,
            memory=None
        )
        
        # Should have valid time context
        assert intent.cognitive_system in [
            CognitiveSystem.SYSTEM_1, CognitiveSystem.SYSTEM_2
        ]

    def test_resolve_with_memory_signal(self, constraint_solver, mock_memory_signal):
        """
        Test resolving with memory signal.
        """
        intent = constraint_solver.resolve(
            query="check price",
            voice=None,
            screen=None,
            time_ctx=None,
            memory=mock_memory_signal
        )
        
        # Memory should influence scoring
        assert intent.confidence >= 0.0

    def test_resolve_all_constraints(self, constraint_solver, mock_voice_features,
                                   mock_screen_context, mock_time_context, mock_memory_signal):
        """
        Test resolving with all constraints.
        """
        intent = constraint_solver.resolve(
            query="check bitcoin price",
            voice=mock_voice_features,
            screen=mock_screen_context,
            time_ctx=mock_time_context,
            memory=mock_memory_signal
        )
        
        # Should have all fields populated
        assert intent.raw_query == "check bitcoin price"
        assert intent.action == "price_check"
        assert intent.target in ["bitcoin", "solana"]
        assert intent.urgency in [
            UrgencyLevel.CRITICAL, UrgencyLevel.HIGH,
            UrgencyLevel.MEDIUM, UrgencyLevel.LOW, UrgencyLevel.MINIMAL
        ]
        assert intent.cognitive_system in [
            CognitiveSystem.SYSTEM_1, CognitiveSystem.SYSTEM_2
        ]
        assert 0.0 <= intent.tau <= 1.0
        assert 0.0 <= intent.confidence <= 1.0
        assert intent.reasoning is not None

    def test_resolve_empty_query(self, constraint_solver):
        """
        Test resolving empty query.
        """
        intent = constraint_solver.resolve(
            query="",
            voice=None,
            screen=None,
            time_ctx=None,
            memory=None
        )
        
        # Should still resolve (may have low confidence)
        assert intent.raw_query == ""

    def test_resolve_ambiguous_query(self, constraint_solver):
        """
        Test resolving ambiguous query.
        """
        intent = constraint_solver.resolve(
            query="check something",
            voice=None,
            screen=None,
            time_ctx=None,
            memory=None
        )
        
        # Should resolve to some action
        assert intent.action in ["price_check", "github_search", "weather_check"]

    def test_resolve_with_memory_fallback_asset(self, constraint_solver, mock_memory_signal):
        """
        Test asset fallback to recent asset from memory.
        """
        screen_ctx = ScreenContext(
            raw_description="",
            detected_assets=[],
            detected_app="",
            detected_numbers=[],
            confidence=0.0
        )
        
        intent = constraint_solver.resolve(
            query="check price",
            voice=None,
            screen=screen_ctx,
            time_ctx=None,
            memory=mock_memory_signal
        )
        
        # Should fall back to memory asset
        assert intent.target in ["BTC", "ETH", "bitcoin"]


# =============================================================================
# Test: Score Template Method (Empty List Fix)
# =============================================================================

class TestScoreTemplate:
    """Test cases for the _score_template method including empty list fixes."""

    def test_score_template_with_empty_keywords(self, constraint_solver):
        """
        Test scoring template with empty keywords (empty list fix).
        """
        template = IntentTemplate(
            action="test_action",
            service="test_service",
            keywords_ar=[],
            keywords_en=[],
            context_signals=["test"],
            weight=1.0
        )
        
        score = constraint_solver._score_template(
            template, "test query", None, None, None, None
        )
        
        # Should handle empty keywords without ZeroDivisionError
        assert isinstance(score, float)
        assert score >= 0.0

    def test_score_template_with_empty_context_signals(self, constraint_solver):
        """
        Test scoring template with empty context signals (empty list fix).
        """
        template = IntentTemplate(
            action="test_action",
            service="test_service",
            keywords_ar=["test"],
            keywords_en=["test"],
            context_signals=[],
            weight=1.0
        )
        
        screen_ctx = ScreenContext(
            raw_description="test content",
            detected_assets=[],
            detected_app="test",
            detected_numbers=[],
            confidence=0.8
        )
        
        score = constraint_solver._score_template(
            template, "test query", None, screen_ctx, None, None
        )
        
        # Should handle empty context signals without ZeroDivisionError
        assert isinstance(score, float)
        assert score >= 0.0

    def test_score_template_with_empty_all_lists(self, constraint_solver):
        """
        Test scoring template with all lists empty (empty list fix).
        """
        template = IntentTemplate(
            action="test_action",
            service="test_service",
            keywords_ar=[],
            keywords_en=[],
            context_signals=[],
            weight=1.0
        )
        
        score = constraint_solver._score_template(
            template, "test query", None, None, None, None
        )
        
        # Should handle all empty lists without ZeroDivisionError
        assert isinstance(score, float)
        assert score >= 0.0

    def test_score_template_keyword_matching(self, constraint_solver):
        """
        Test keyword matching in scoring.
        """
        template = IntentTemplate(
            action="price_check",
            service="coingecko",
            keywords_ar=["bitcoin", "btc"],
            keywords_en=["bitcoin", "btc"],
            context_signals=[],
            weight=1.0
        )
        
        # Query with keyword
        score1 = constraint_solver._score_template(
            template, "check bitcoin price", None, None, None, None
        )
        
        # Query without keyword
        score2 = constraint_solver._score_template(
            template, "check weather", None, None, None, None
        )
        
        # Score with keyword should be higher
        assert score1 > score2

    def test_score_template_context_matching(self, constraint_solver):
        """
        Test context matching in scoring.
        """
        template = IntentTemplate(
            action="price_check",
            service="coingecko",
            keywords_ar=[],
            keywords_en=[],
            context_signals=["binance", "crypto"],
            weight=1.0
        )
        
        screen_ctx1 = ScreenContext(
            raw_description="Binance trading",
            detected_assets=[],
            detected_app="Binance",
            detected_numbers=[],
            confidence=0.8
        )
        
        screen_ctx2 = ScreenContext(
            raw_description="GitHub repository",
            detected_assets=[],
            detected_app="GitHub",
            detected_numbers=[],
            confidence=0.8
        )
        
        score1 = constraint_solver._score_template(
            template, "check price", None, screen_ctx1, None, None
        )
        
        score2 = constraint_solver._score_template(
            template, "check price", None, screen_ctx2, None, None
        )
        
        # Score with matching context should be higher
        assert score1 > score2

    def test_score_template_memory_bias(self, constraint_solver):
        """
        Test memory recency bias in scoring.
        """
        template = IntentTemplate(
            action="price_check",
            service="coingecko",
            keywords_ar=[],
            keywords_en=[],
            context_signals=[],
            weight=1.0
        )
        
        memory1 = MemorySignal(
            recent_services=["coingecko"],
            recent_assets=[],
            last_action=None,
            query_count_1h=0
        )
        
        memory2 = MemorySignal(
            recent_services=["github"],
            recent_assets=[],
            last_action=None,
            query_count_1h=0
        )
        
        score1 = constraint_solver._score_template(
            template, "check price", None, None, None, memory1
        )
        
        score2 = constraint_solver._score_template(
            template, "check price", None, None, None, memory2
        )
        
        # Score with matching service in memory should be higher
        assert score1 > score2

    def test_score_template_time_context_bonus(self, constraint_solver):
        """
        Test time context bonus in scoring.
        """
        template = IntentTemplate(
            action="price_check",
            service="coingecko",
            keywords_ar=[],
            keywords_en=[],
            context_signals=[],
            weight=1.0
        )
        
        time_ctx1 = TimeContext(
            hour=15,
            is_market_hours=True,
            day_of_week=1,
            is_weekend=False,
            market_session="open"
        )
        
        time_ctx2 = TimeContext(
            hour=2,
            is_market_hours=False,
            day_of_week=1,
            is_weekend=False,
            market_session="pre"
        )
        
        score1 = constraint_solver._score_template(
            template, "check price", None, None, time_ctx1, None
        )
        
        score2 = constraint_solver._score_template(
            template, "check price", None, None, time_ctx2, None
        )
        
        # Score during market hours should be higher
        assert score1 > score2

    def test_score_template_weight_application(self, constraint_solver):
        """
        Test that template weight is applied correctly.
        """
        template1 = IntentTemplate(
            action="test_action",
            service="test_service",
            keywords_ar=["test"],
            keywords_en=["test"],
            context_signals=[],
            weight=1.0
        )
        
        template2 = IntentTemplate(
            action="test_action",
            service="test_service",
            keywords_ar=["test"],
            keywords_en=["test"],
            context_signals=[],
            weight=2.0
        )
        
        score1 = constraint_solver._score_template(
            template1, "test query", None, None, None, None
        )
        
        score2 = constraint_solver._score_template(
            template2, "test query", None, None, None, None
        )
        
        # Higher weight should produce higher score
        assert score2 > score1


# =============================================================================
# Test: Build Reasoning Method
# =============================================================================

class TestBuildReasoning:
    """Test cases for the _build_reasoning method."""

    def test_build_reasoning_with_high_score(self, constraint_solver):
        """
        Test building reasoning with high score.
        """
        template = IntentTemplate(
            action="price_check",
            service="coingecko",
            keywords_ar=["bitcoin"],
            keywords_en=["bitcoin"],
            context_signals=[],
            weight=1.0
        )
        
        reasoning = constraint_solver._build_reasoning(
            template, 0.8, None, None, None
        )
        
        assert "keyword match" in reasoning.lower()

    def test_build_reasoning_with_screen_context(self, constraint_solver, mock_screen_context):
        """
        Test building reasoning with screen context.
        """
        template = IntentTemplate(
            action="price_check",
            service="coingecko",
            keywords_ar=[],
            keywords_en=[],
            context_signals=[],
            weight=1.0
        )
        
        reasoning = constraint_solver._build_reasoning(
            template, 0.5, None, mock_screen_context, None
        )
        
        assert "screen shows" in reasoning.lower()

    def test_build_reasoning_with_voice_urgency(self, constraint_solver, mock_voice_features):
        """
        Test building reasoning with high voice urgency.
        """
        template = IntentTemplate(
            action="test_action",
            service="test_service",
            keywords_ar=[],
            keywords_en=[],
            context_signals=[],
            weight=1.0
        )
        
        # Create high urgency voice
        high_urgency_voice = VoiceFeatures(
            speech_rate_wpm=250.0,
            pitch_variance=1.0,
            volume_db=80.0,
            pause_frequency=0.0,
            transcript="urgent",
            language="en"
        )
        
        reasoning = constraint_solver._build_reasoning(
            template, 0.5, high_urgency_voice, None, None
        )
        
        assert "stressed voice" in reasoning.lower()

    def test_build_reasoning_with_memory_context(self, constraint_solver, mock_memory_signal):
        """
        Test building reasoning with memory context.
        """
        template = IntentTemplate(
            action="price_check",
            service="coingecko",
            keywords_ar=[],
            keywords_en=[],
            context_signals=[],
            weight=1.0
        )
        
        reasoning = constraint_solver._build_reasoning(
            template, 0.5, None, None, mock_memory_signal
        )
        
        assert "recent conversation" in reasoning.lower()

    def test_build_reasoning_default(self, constraint_solver):
        """
        Test building reasoning with no context.
        """
        template = IntentTemplate(
            action="test_action",
            service="test_service",
            keywords_ar=[],
            keywords_en=[],
            context_signals=[],
            weight=1.0
        )
        
        reasoning = constraint_solver._build_reasoning(
            template, 0.1, None, None, None
        )
        
        assert reasoning == "default inference"


# =============================================================================
# Test: Build Time Context
# =============================================================================

class TestBuildTimeContext:
    """Test cases for the build_time_context function."""

    def test_build_time_context_structure(self):
        """
        Test that build_time_context returns valid TimeContext.
        """
        ctx = build_time_context()
        
        assert isinstance(ctx, TimeContext)
        assert 0 <= ctx.hour <= 23
        assert 0 <= ctx.day_of_week <= 6
        assert isinstance(ctx.is_market_hours, bool)
        assert isinstance(ctx.is_weekend, bool)
        assert ctx.market_session in ["pre", "open", "after"]

    def test_build_time_context_weekend_detection(self):
        """
        Test weekend detection in time context.
        """
        with patch('agent.aether_forge.constraint_solver.datetime') as mock_dt:
            # Saturday (day 5)
            mock_dt.utcnow.return_value = datetime(2024, 1, 6, 12, 0, 0)
            ctx = build_time_context()
            assert ctx.is_weekend is True
            
            # Monday (day 0)
            mock_dt.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0)
            ctx = build_time_context()
            assert ctx.is_weekend is False

    def test_build_time_context_market_hours(self):
        """
        Test market hours detection in time context.
        """
        with patch('agent.aether_forge.constraint_solver.datetime') as mock_dt:
            # During market hours (15:00 UTC, Monday)
            mock_dt.utcnow.return_value = datetime(2024, 1, 1, 15, 0, 0)
            ctx = build_time_context()
            assert ctx.is_market_hours is True
            
            # Outside market hours (8:00 UTC, Monday)
            mock_dt.utcnow.return_value = datetime(2024, 1, 1, 8, 0, 0)
            ctx = build_time_context()
            assert ctx.is_market_hours is False


# =============================================================================
# Test: Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test cases for edge cases and boundary conditions."""

    def test_resolve_with_none_all_constraints(self, constraint_solver):
        """
        Test resolving with all constraints as None.
        """
        intent = constraint_solver.resolve(
            query="test",
            voice=None,
            screen=None,
            time_ctx=None,
            memory=None
        )
        
        # Should still resolve
        assert intent.action is not None
        assert intent.raw_query == "test"

    def test_extract_asset_with_none_screen_context(self):
        """
        Test extract_asset with None screen context.
        """
        asset = extract_asset("bitcoin price", None)
        assert asset == "bitcoin"

    def test_extract_asset_with_empty_screen_assets(self):
        """
        Test extract_asset with empty screen assets.
        """
        screen_ctx = ScreenContext(
            raw_description="",
            detected_assets=[],
            detected_app="",
            detected_numbers=[],
            confidence=0.0
        )
        
        asset = extract_asset("check price", screen_ctx)
        assert asset is None

    def test_score_template_with_none_screen(self, constraint_solver):
        """
        Test score_template with None screen context.
        """
        template = IntentTemplate(
            action="test_action",
            service="test_service",
            keywords_ar=["test"],
            keywords_en=["test"],
            context_signals=["test"],
            weight=1.0
        )
        
        score = constraint_solver._score_template(
            template, "test query", None, None, None, None
        )
        
        # Should handle None screen gracefully
        assert isinstance(score, float)

    def test_compute_tau_boundary_values(self):
        """
        Test compute_tau at boundary values.
        """
        # Test at exact boundaries
        tau1, _ = compute_tau(0.0)
        tau2, _ = compute_tau(1.0)
        
        assert tau1 == pytest.approx(TAU_MAX, rel=1e-6)
        assert tau2 == pytest.approx(TAU_MIN, rel=1e-6)

    def test_classify_urgency_negative_value(self):
        """
        Test classify_urgency with negative value.
        """
        level = classify_urgency(-0.5)
        assert level == UrgencyLevel.MINIMAL

    def test_classify_urgency_value_above_one(self):
        """
        Test classify_urgency with value above 1.0.
        """
        level = classify_urgency(1.5)
        assert level == UrgencyLevel.CRITICAL

    def test_memory_signal_empty_lists(self):
        """
        Test MemorySignal with empty lists.
        """
        signal = MemorySignal()
        
        assert signal.recent_services == []
        assert signal.recent_assets == []
        assert signal.last_action is None
        assert signal.query_count_1h == 0
