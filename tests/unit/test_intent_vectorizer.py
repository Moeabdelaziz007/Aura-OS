"""
Unit Tests for Intent Vectorizer Module

Tests the intent vectorization logic including the zero vector fix.
"""

import pytest
import numpy as np
from unittest.mock import patch


# =============================================================================
# Import the module under test
# =============================================================================

from agent.core.intent_vectorizer import IntentVectorizer


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def intent_vectorizer_local():
    """
    Create an IntentVectorizer instance with local mode.
    """
    return IntentVectorizer(use_remote=False)


@pytest.fixture
def intent_vectorizer_remote():
    """
    Create an IntentVectorizer instance with remote mode.
    """
    return IntentVectorizer(use_remote=True)


@pytest.fixture
def sample_texts():
    """
    Sample texts for vectorization.
    """
    return [
        "check bitcoin price",
        "search github repository",
        "what's the weather in cairo",
        "buy ethereum now",
        "show me solana chart"
    ]


@pytest.fixture
def sample_candidates():
    """
    Sample candidate intents for nearest neighbor search.
    """
    return [
        {
            "intent": "check price",
            "vector": [0.1, 0.2, 0.3] + [0.0] * 765,
            "service": "coingecko"
        },
        {
            "intent": "search repo",
            "vector": [0.4, 0.5, 0.6] + [0.0] * 765,
            "service": "github"
        },
        {
            "intent": "weather check",
            "vector": [0.7, 0.8, 0.9] + [0.0] * 765,
            "service": "weather"
        }
    ]


# =============================================================================
# Test: IntentVectorizer Initialization
# =============================================================================

class TestIntentVectorizerInitialization:
    """Test cases for IntentVectorizer initialization."""

    def test_initialization_local_mode(self):
        """
        Test initialization with local mode.
        """
        vectorizer = IntentVectorizer(use_remote=False)
        assert vectorizer.use_remote is False
        assert vectorizer.embedding_dim == 768

    def test_initialization_remote_mode(self):
        """
        Test initialization with remote mode.
        """
        vectorizer = IntentVectorizer(use_remote=True)
        assert vectorizer.use_remote is True
        assert vectorizer.embedding_dim == 768

    def test_initialization_default_embedding_dim(self):
        """
        Test that embedding dimension defaults to 768.
        """
        vectorizer = IntentVectorizer()
        assert vectorizer.embedding_dim == 768


# =============================================================================
# Test: Vectorize Method
# =============================================================================

class TestVectorize:
    """Test cases for the vectorize method."""

    @pytest.mark.asyncio
    async def test_vectorize_local_mode(self, intent_vectorizer_local):
        """
        Test vectorizing text in local mode.
        """
        text = "check bitcoin price"
        vector = await intent_vectorizer_local.vectorize(text)
        
        assert isinstance(vector, list)
        assert len(vector) == 768
        assert all(isinstance(x, float) for x in vector)

    @pytest.mark.asyncio
    async def test_vectorize_remote_mode(self, intent_vectorizer_remote):
        """
        Test vectorizing text in remote mode.
        """
        text = "check bitcoin price"
        vector = await intent_vectorizer_remote.vectorize(text)
        
        # Remote mode returns zero vector (placeholder)
        assert isinstance(vector, list)
        assert len(vector) == 768
        assert all(x == 0.0 for x in vector)

    @pytest.mark.asyncio
    async def test_vectorize_deterministic_local(self, intent_vectorizer_local):
        """
        Test that local vectorization is deterministic.
        """
        text = "deterministic text"
        vector1 = await intent_vectorizer_local.vectorize(text)
        vector2 = await intent_vectorizer_local.vectorize(text)
        
        # Same text should produce same vector
        assert vector1 == vector2

    @pytest.mark.asyncio
    async def test_vectorize_different_texts_different_vectors(self, intent_vectorizer_local):
        """
        Test that different texts produce different vectors.
        """
        text1 = "text one"
        text2 = "text two"
        
        vector1 = await intent_vectorizer_local.vectorize(text1)
        vector2 = await intent_vectorizer_local.vectorize(text2)
        
        # Different texts should produce different vectors
        assert vector1 != vector2

    @pytest.mark.asyncio
    async def test_vectorize_empty_string(self, intent_vectorizer_local):
        """
        Test vectorizing empty string.
        """
        vector = await intent_vectorizer_local.vectorize("")
        
        assert isinstance(vector, list)
        assert len(vector) == 768

    @pytest.mark.asyncio
    async def test_vectorize_special_characters(self, intent_vectorizer_local):
        """
        Test vectorizing text with special characters.
        """
        text = "text with !@#$%^&*() and symbols"
        vector = await intent_vectorizer_local.vectorize(text)
        
        assert isinstance(vector, list)
        assert len(vector) == 768

    @pytest.mark.asyncio
    async def test_vectorize_unicode(self, intent_vectorizer_local):
        """
        Test vectorizing text with unicode characters.
        """
        text = "مرحبا بالعالم 🌍"
        vector = await intent_vectorizer_local.vectorize(text)
        
        assert isinstance(vector, list)
        assert len(vector) == 768

    @pytest.mark.asyncio
    async def test_vectorize_very_long_text(self, intent_vectorizer_local):
        """
        Test vectorizing very long text.
        """
        text = "x" * 10000
        vector = await intent_vectorizer_local.vectorize(text)
        
        assert isinstance(vector, list)
        assert len(vector) == 768

    @pytest.mark.asyncio
    async def test_vectorize_whitespace_only(self, intent_vectorizer_local):
        """
        Test vectorizing whitespace-only text.
        """
        text = "   \t\n  "
        vector = await intent_vectorizer_local.vectorize(text)
        
        assert isinstance(vector, list)
        assert len(vector) == 768


# =============================================================================
# Test: Calculate Similarity Method
# =============================================================================

class TestCalculateSimilarity:
    """Test cases for the calculate_similarity method."""

    def test_calculate_similarity_identical_vectors(self, intent_vectorizer_local):
        """
        Test similarity of identical vectors.
        """
        vec = [0.5, 0.3, 0.7] + [0.0] * 765
        similarity = intent_vectorizer_local.calculate_similarity(vec, vec)
        
        # Identical vectors should have similarity of 1.0
        assert similarity == pytest.approx(1.0, rel=1e-6)

    def test_calculate_similarity_orthogonal_vectors(self, intent_vectorizer_local):
        """
        Test similarity of orthogonal vectors.
        """
        vec_a = [1.0, 0.0] + [0.0] * 766
        vec_b = [0.0, 1.0] + [0.0] * 766
        similarity = intent_vectorizer_local.calculate_similarity(vec_a, vec_b)
        
        # Orthogonal vectors should have similarity of 0.0
        assert similarity == pytest.approx(0.0, abs=1e-6)

    def test_calculate_similarity_opposite_vectors(self, intent_vectorizer_local):
        """
        Test similarity of opposite vectors.
        """
        vec_a = [1.0, 0.5] + [0.0] * 766
        vec_b = [-1.0, -0.5] + [0.0] * 766
        similarity = intent_vectorizer_local.calculate_similarity(vec_a, vec_b)
        
        # Opposite vectors should have similarity of -1.0
        assert similarity == pytest.approx(-1.0, rel=1e-6)

    def test_calculate_similarity_zero_vector_a(self, intent_vectorizer_local):
        """
        Test similarity with zero vector (first argument).
        """
        vec_a = [0.0] * 768
        vec_b = [0.5, 0.3, 0.7] + [0.0] * 765
        similarity = intent_vectorizer_local.calculate_similarity(vec_a, vec_b)
        
        # Zero vector should return 0.0 (zero division fix)
        assert similarity == 0.0

    def test_calculate_similarity_zero_vector_b(self, intent_vectorizer_local):
        """
        Test similarity with zero vector (second argument).
        """
        vec_a = [0.5, 0.3, 0.7] + [0.0] * 765
        vec_b = [0.0] * 768
        similarity = intent_vectorizer_local.calculate_similarity(vec_a, vec_b)
        
        # Zero vector should return 0.0 (zero division fix)
        assert similarity == 0.0

    def test_calculate_similarity_both_zero_vectors(self, intent_vectorizer_local):
        """
        Test similarity when both vectors are zero.
        """
        vec_a = [0.0] * 768
        vec_b = [0.0] * 768
        similarity = intent_vectorizer_local.calculate_similarity(vec_a, vec_b)
        
        # Both zero vectors should return 0.0 (zero division fix)
        assert similarity == 0.0

    def test_calculate_similarity_partial_zero_vector(self, intent_vectorizer_local):
        """
        Test similarity with partially zero vector.
        """
        vec_a = [0.5, 0.0, 0.0] + [0.0] * 765
        vec_b = [0.3, 0.0, 0.0] + [0.0] * 765
        similarity = intent_vectorizer_local.calculate_similarity(vec_a, vec_b)
        
        # Should handle partial zero vectors
        assert isinstance(similarity, float)
        assert -1.0 <= similarity <= 1.0

    def test_calculate_similarity_range(self, intent_vectorizer_local):
        """
        Test that similarity is always in range [-1, 1].
        """
        vec_a = [0.5, 0.3, 0.7] + [0.0] * 765
        vec_b = [0.2, 0.8, 0.1] + [0.0] * 765
        similarity = intent_vectorizer_local.calculate_similarity(vec_a, vec_b)
        
        assert -1.0 <= similarity <= 1.0

    def test_calculate_similarity_different_lengths_raises_error(self, intent_vectorizer_local):
        """
        Test that vectors of different lengths raise error.
        """
        vec_a = [0.5, 0.3, 0.7]
        vec_b = [0.2, 0.8, 0.1, 0.4]
        
        # Should raise ValueError due to shape mismatch
        with pytest.raises(ValueError):
            intent_vectorizer_local.calculate_similarity(vec_a, vec_b)


# =============================================================================
# Test: Get Nearest Neighbors Method
# =============================================================================

class TestGetNearestNeighbors:
    """Test cases for the get_nearest_neighbors method."""

    @pytest.mark.asyncio
    async def test_get_nearest_neighbors_basic(self, intent_vectorizer_local, sample_candidates):
        """
        Test basic nearest neighbor search.
        """
        query = "check price"
        results = await intent_vectorizer_local.get_nearest_neighbors(
            query, sample_candidates, top_k=2
        )
        
        assert len(results) == 2
        assert "similarity_score" in results[0]
        assert "similarity_score" in results[1]

    @pytest.mark.asyncio
    async def test_get_nearest_neighbors_sorted_by_similarity(self, intent_vectorizer_local, sample_candidates):
        """
        Test that results are sorted by similarity descending.
        """
        query = "check price"
        results = await intent_vectorizer_local.get_nearest_neighbors(
            query, sample_candidates, top_k=3
        )
        
        # Check that results are sorted by similarity
        for i in range(len(results) - 1):
            assert results[i]["similarity_score"] >= results[i + 1]["similarity_score"]

    @pytest.mark.asyncio
    async def test_get_nearest_neighbors_top_k_limit(self, intent_vectorizer_local, sample_candidates):
        """
        Test that top_k parameter limits results.
        """
        query = "search"
        results = await intent_vectorizer_local.get_nearest_neighbors(
            query, sample_candidates, top_k=1
        )
        
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_nearest_neighbors_top_k_greater_than_candidates(self, intent_vectorizer_local, sample_candidates):
        """
        Test when top_k is greater than number of candidates.
        """
        query = "search"
        results = await intent_vectorizer_local.get_nearest_neighbors(
            query, sample_candidates, top_k=100
        )
        
        # Should return all candidates
        assert len(results) == len(sample_candidates)

    @pytest.mark.asyncio
    async def test_get_nearest_neighbors_empty_candidates(self, intent_vectorizer_local):
        """
        Test with empty candidates list.
        """
        query = "search"
        results = await intent_vectorizer_local.get_nearest_neighbors(query, [], top_k=3)
        
        assert results == []

    @pytest.mark.asyncio
    async def test_get_nearest_neighbors_candidate_without_vector(self, intent_vectorizer_local):
        """
        Test handling candidates without vector field.
        """
        candidates = [
            {"intent": "no vector", "service": "unknown"},  # No vector
            {
                "intent": "has vector",
                "vector": [0.1, 0.2, 0.3] + [0.0] * 765,
                "service": "coingecko"
            }
        ]
        query = "search"
        results = await intent_vectorizer_local.get_nearest_neighbors(query, candidates, top_k=2)
        
        # Should only return candidates with vectors
        assert len(results) == 1
        assert results[0]["intent"] == "has vector"

    @pytest.mark.asyncio
    async def test_get_nearest_neighbors_preserves_original_fields(self, intent_vectorizer_local, sample_candidates):
        """
        Test that original candidate fields are preserved.
        """
        query = "search"
        results = await intent_vectorizer_local.get_nearest_neighbors(
            query, sample_candidates, top_k=1
        )
        
        # Check that original fields are present
        assert "intent" in results[0]
        assert "service" in results[0]
        assert "vector" in results[0]

    @pytest.mark.asyncio
    async def test_get_nearest_neighbors_default_top_k(self, intent_vectorizer_local, sample_candidates):
        """
        Test with default top_k value (3).
        """
        query = "search"
        results = await intent_vectorizer_local.get_nearest_neighbors(query, sample_candidates)
        
        # Default top_k is 3
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_get_nearest_neighbors_top_k_zero(self, intent_vectorizer_local, sample_candidates):
        """
        Test with top_k of 0.
        """
        query = "search"
        results = await intent_vectorizer_local.get_nearest_neighbors(query, sample_candidates, top_k=0)
        
        assert results == []

    @pytest.mark.asyncio
    async def test_get_nearest_candidates_all_without_vectors(self, intent_vectorizer_local):
        """
        Test when all candidates lack vectors.
        """
        candidates = [
            {"intent": "no vector 1"},
            {"intent": "no vector 2"},
            {"intent": "no vector 3"}
        ]
        query = "search"
        results = await intent_vectorizer_local.get_nearest_neighbors(query, candidates, top_k=3)
        
        # Should return empty list
        assert results == []


# =============================================================================
# Test: Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test cases for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_vectorize_none_text(self, intent_vectorizer_local):
        """
        Test vectorizing None text.
        """
        # Should raise TypeError
        with pytest.raises(TypeError):
            await intent_vectorizer_local.vectorize(None)

    @pytest.mark.asyncio
    async def test_vectorize_numeric_input(self, intent_vectorizer_local):
        """
        Test vectorizing numeric input.
        """
        # Should raise TypeError
        with pytest.raises(TypeError):
            await intent_vectorizer_local.vectorize(123)

    def test_calculate_similarity_empty_vectors(self, intent_vectorizer_local):
        """
        Test similarity with empty vectors.
        """
        vec_a = []
        vec_b = []
        
        # Empty vectors are handled gracefully (returns 0.0)
        similarity = intent_vectorizer_local.calculate_similarity(vec_a, vec_b)
        assert similarity == 0.0

    def test_calculate_similarity_single_element_vectors(self, intent_vectorizer_local):
        """
        Test similarity with single-element vectors.
        """
        vec_a = [1.0]
        vec_b = [1.0]
        similarity = intent_vectorizer_local.calculate_similarity(vec_a, vec_b)
        
        assert similarity == pytest.approx(1.0, rel=1e-6)

    def test_calculate_similarity_negative_values(self, intent_vectorizer_local):
        """
        Test similarity with negative vector values.
        """
        vec_a = [-0.5, -0.3, -0.7] + [0.0] * 765
        vec_b = [-0.2, -0.8, -0.1] + [0.0] * 765
        similarity = intent_vectorizer_local.calculate_similarity(vec_a, vec_b)
        
        assert isinstance(similarity, float)
        assert -1.0 <= similarity <= 1.0

    def test_calculate_similarity_very_large_values(self, intent_vectorizer_local):
        """
        Test similarity with very large vector values.
        """
        vec_a = [1e10, 2e10, 3e10] + [0.0] * 765
        vec_b = [4e10, 5e10, 6e10] + [0.0] * 765
        similarity = intent_vectorizer_local.calculate_similarity(vec_a, vec_b)
        
        # Should still produce valid result
        assert isinstance(similarity, float)
        assert -1.0 <= similarity <= 1.0

    def test_calculate_similarity_very_small_values(self, intent_vectorizer_local):
        """
        Test similarity with very small vector values.
        """
        vec_a = [1e-10, 2e-10, 3e-10] + [0.0] * 765
        vec_b = [4e-10, 5e-10, 6e-10] + [0.0] * 765
        similarity = intent_vectorizer_local.calculate_similarity(vec_a, vec_b)
        
        # Should still produce valid result
        assert isinstance(similarity, float)
        assert -1.0 <= similarity <= 1.0

    @pytest.mark.asyncio
    async def test_get_nearest_neighbors_with_duplicate_vectors(self, intent_vectorizer_local):
        """
        Test nearest neighbors with duplicate vectors.
        """
        vector = [0.1, 0.2, 0.3] + [0.0] * 765
        candidates = [
            {"intent": "same 1", "vector": vector},
            {"intent": "same 2", "vector": vector},
            {"intent": "same 3", "vector": vector}
        ]
        # Use query that produces same vector as candidates
        query = "same 1"  # This will produce the same vector as the candidates
        results = await intent_vectorizer_local.get_nearest_neighbors(query, candidates, top_k=3)
        
        # All should have similarity of 1.0 (convert generator to list)
        assert all(r["similarity_score"] == pytest.approx(1.0, rel=1e-6) for r in list(results))

    @pytest.mark.asyncio
    async def test_vectorize_consistency_across_instances(self):
        """
        Test that same text produces same vector across instances.
        """
        text = "consistent text"
        vectorizer1 = IntentVectorizer(use_remote=False)
        vectorizer2 = IntentVectorizer(use_remote=False)
        
        vec1 = await vectorizer1.vectorize(text)
        vec2 = await vectorizer2.vectorize(text)
        
        # Should be identical
        assert vec1 == vec2
