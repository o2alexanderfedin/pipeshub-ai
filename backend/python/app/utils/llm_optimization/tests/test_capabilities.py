"""
Unit tests for provider capabilities module.

Tests provider detection, capability queries, and discount calculations.
Target: 90%+ coverage
"""

import pytest
from app.utils.llm_optimization.capabilities import (
    ProviderCapability,
    ProviderCapabilities,
    OptimizationType,
)
from app.utils.aimodels import LLMProvider


class TestProviderCapability:
    """Test ProviderCapability dataclass."""

    def test_create_valid_capability(self) -> None:
        """Test creating capability with valid data."""
        cap = ProviderCapability(
            provider="anthropic",
            supports_batch=True,
            supports_caching=True,
            batch_max_size=10000,
            batch_discount_percent=50,
            cache_discount_percent=90,
        )

        assert cap.provider == "anthropic"
        assert cap.supports_batch is True
        assert cap.supports_caching is True
        assert cap.batch_max_size == 10000
        assert cap.batch_discount_percent == 50
        assert cap.cache_discount_percent == 90

    def test_capability_immutable(self) -> None:
        """Test that capability is immutable (frozen dataclass)."""
        cap = ProviderCapability(
            provider="test",
            supports_batch=True,
            supports_caching=False,
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            cap.supports_batch = False  # type: ignore

    def test_invalid_batch_discount(self) -> None:
        """Test validation of batch discount percentage."""
        with pytest.raises(ValueError, match="Batch discount must be 0-100"):
            ProviderCapability(
                provider="test",
                supports_batch=True,
                supports_caching=False,
                batch_discount_percent=150,  # Invalid: > 100
            )

        with pytest.raises(ValueError, match="Batch discount must be 0-100"):
            ProviderCapability(
                provider="test",
                supports_batch=True,
                supports_caching=False,
                batch_discount_percent=-10,  # Invalid: < 0
            )

    def test_invalid_cache_discount(self) -> None:
        """Test validation of cache discount percentage."""
        with pytest.raises(ValueError, match="Cache discount must be 0-100"):
            ProviderCapability(
                provider="test",
                supports_batch=False,
                supports_caching=True,
                cache_discount_percent=200,  # Invalid: > 100
            )

    def test_invalid_batch_max_size(self) -> None:
        """Test validation of batch max size."""
        with pytest.raises(ValueError, match="Batch max size must be positive"):
            ProviderCapability(
                provider="test",
                supports_batch=True,
                supports_caching=False,
                batch_max_size=0,  # Invalid: not positive
            )

    def test_combined_discount_both_optimizations(self) -> None:
        """Test combined discount calculation with both optimizations."""
        cap = ProviderCapability(
            provider="anthropic",
            supports_batch=True,
            supports_caching=True,
            batch_discount_percent=50,  # Pay 50%
            cache_discount_percent=90,  # Pay 10% on cached
        )

        # Combined: 0.5 * 0.1 = 0.05 = 5% payment = 95% discount
        assert cap.combined_discount_percent == 95

    def test_combined_discount_batch_only(self) -> None:
        """Test combined discount with batch only."""
        cap = ProviderCapability(
            provider="test",
            supports_batch=True,
            supports_caching=False,
            batch_discount_percent=50,
        )

        assert cap.combined_discount_percent == 50

    def test_combined_discount_cache_only(self) -> None:
        """Test combined discount with cache only."""
        cap = ProviderCapability(
            provider="test",
            supports_batch=False,
            supports_caching=True,
            cache_discount_percent=90,
        )

        assert cap.combined_discount_percent == 90

    def test_combined_discount_none(self) -> None:
        """Test combined discount with no optimizations."""
        cap = ProviderCapability(
            provider="test",
            supports_batch=False,
            supports_caching=False,
        )

        assert cap.combined_discount_percent == 0


class TestProviderCapabilities:
    """Test ProviderCapabilities registry."""

    def test_get_anthropic_capability(self) -> None:
        """Test getting Anthropic capabilities (Phase 1 supported provider)."""
        cap = ProviderCapabilities.get(LLMProvider.ANTHROPIC.value)

        assert cap.provider == LLMProvider.ANTHROPIC.value
        assert cap.supports_batch is True
        assert cap.supports_caching is True
        assert cap.batch_max_size == 10000
        assert cap.batch_discount_percent == 50
        assert cap.cache_discount_percent == 90

    def test_get_unsupported_provider(self) -> None:
        """Test getting capabilities for unsupported provider."""
        # Ollama not supported in Phase 1
        cap = ProviderCapabilities.get(LLMProvider.OLLAMA.value)

        assert cap.provider == LLMProvider.OLLAMA.value
        assert cap.supports_batch is False
        assert cap.supports_caching is False
        assert cap.batch_max_size is None
        assert cap.batch_discount_percent == 0
        assert cap.cache_discount_percent == 0

    def test_supports_batch_anthropic(self) -> None:
        """Test batch support detection for Anthropic."""
        assert ProviderCapabilities.supports_batch(LLMProvider.ANTHROPIC.value) is True

    def test_supports_batch_unsupported(self) -> None:
        """Test batch support detection for unsupported provider."""
        assert ProviderCapabilities.supports_batch(LLMProvider.OLLAMA.value) is False

    def test_supports_caching_anthropic(self) -> None:
        """Test caching support detection for Anthropic."""
        assert ProviderCapabilities.supports_caching(LLMProvider.ANTHROPIC.value) is True

    def test_supports_caching_unsupported(self) -> None:
        """Test caching support detection for unsupported provider."""
        assert ProviderCapabilities.supports_caching(LLMProvider.OLLAMA.value) is False

    def test_supports_any_optimization_anthropic(self) -> None:
        """Test any optimization support for Anthropic."""
        assert ProviderCapabilities.supports_any_optimization(LLMProvider.ANTHROPIC.value) is True

    def test_supports_any_optimization_unsupported(self) -> None:
        """Test any optimization support for unsupported provider."""
        assert ProviderCapabilities.supports_any_optimization(LLMProvider.OLLAMA.value) is False

    def test_get_batch_max_size_anthropic(self) -> None:
        """Test getting batch max size for Anthropic."""
        max_size = ProviderCapabilities.get_batch_max_size(LLMProvider.ANTHROPIC.value)
        assert max_size == 10000

    def test_get_batch_max_size_unsupported(self) -> None:
        """Test getting batch max size for unsupported provider."""
        max_size = ProviderCapabilities.get_batch_max_size(LLMProvider.OLLAMA.value)
        assert max_size is None

    def test_list_supported_providers(self) -> None:
        """Test listing providers with optimization support."""
        supported = ProviderCapabilities.list_supported_providers()

        # Phase 1: Only Anthropic
        assert LLMProvider.ANTHROPIC.value in supported
        assert len(supported) >= 1  # At least Anthropic

    def test_get_optimization_summary_anthropic(self) -> None:
        """Test getting optimization summary for Anthropic."""
        summary = ProviderCapabilities.get_optimization_summary(LLMProvider.ANTHROPIC.value)

        assert summary["provider"] == LLMProvider.ANTHROPIC.value
        assert summary["supports_batch"] is True
        assert summary["supports_caching"] is True
        assert summary["batch_max_size"] == 10000
        assert summary["batch_discount"] == "50%"
        assert summary["cache_discount"] == "90%"
        assert summary["combined_discount"] == "95%"
        assert "95%" in summary["potential_savings"]
        assert "Batch API" in summary["potential_savings"]
        assert "Caching" in summary["potential_savings"]

    def test_get_optimization_summary_unsupported(self) -> None:
        """Test getting optimization summary for unsupported provider."""
        summary = ProviderCapabilities.get_optimization_summary(LLMProvider.OLLAMA.value)

        assert summary["provider"] == LLMProvider.OLLAMA.value
        assert summary["supports_batch"] is False
        assert summary["supports_caching"] is False
        assert summary["potential_savings"] == "No optimizations available"


class TestOptimizationType:
    """Test OptimizationType enum."""

    def test_optimization_types(self) -> None:
        """Test optimization type enum values."""
        assert OptimizationType.BATCH_API.value == "batch_api"
        assert OptimizationType.PROMPT_CACHING.value == "prompt_caching"

    def test_optimization_type_str(self) -> None:
        """Test optimization type string conversion."""
        assert OptimizationType.BATCH_API.value == "batch_api"
        assert OptimizationType.PROMPT_CACHING.value == "prompt_caching"
