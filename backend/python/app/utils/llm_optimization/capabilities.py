"""
Provider capability detection for LLM optimizations.

Determines which optimization features (Batch API, Prompt Caching) are
supported by each LLM provider.

Follows Open/Closed Principle: Easy to add new providers without
modifying existing code.
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum

from app.utils.aimodels import LLMProvider


class OptimizationType(str, Enum):
    """Types of LLM optimizations."""

    BATCH_API = "batch_api"
    PROMPT_CACHING = "prompt_caching"


@dataclass(frozen=True)
class ProviderCapability:
    """
    Immutable capability information for a provider.

    Attributes:
        provider: Provider identifier
        supports_batch: Whether provider supports Batch API
        supports_caching: Whether provider supports Prompt Caching
        batch_max_size: Maximum batch size (None if unsupported)
        batch_discount_percent: Cost discount for batch API (0-100)
        cache_discount_percent: Cost discount for caching (0-100)
    """

    provider: str
    supports_batch: bool
    supports_caching: bool
    batch_max_size: Optional[int] = None
    batch_discount_percent: int = 0
    cache_discount_percent: int = 0

    def __post_init__(self) -> None:
        """Validate capability data."""
        if self.batch_discount_percent < 0 or self.batch_discount_percent > 100:
            raise ValueError("Batch discount must be 0-100")
        if self.cache_discount_percent < 0 or self.cache_discount_percent > 100:
            raise ValueError("Cache discount must be 0-100")
        if self.batch_max_size is not None and self.batch_max_size < 1:
            raise ValueError("Batch max size must be positive")

    @property
    def combined_discount_percent(self) -> int:
        """
        Calculate combined discount when both optimizations used.

        For most providers, discounts stack multiplicatively:
        - Batch: 50% off = pay 50%
        - Cache: 90% off cached tokens = pay 10% on cached
        - Combined: 0.5 * 0.1 = 0.05 = pay 5% = 95% discount

        Returns:
            Combined discount percentage (0-100)
        """
        if not self.supports_batch or not self.cache_discount_percent:
            return max(self.batch_discount_percent, self.cache_discount_percent)

        # Convert discounts to multipliers, multiply, convert back
        batch_multiplier = 1 - (self.batch_discount_percent / 100)
        cache_multiplier = 1 - (self.cache_discount_percent / 100)
        combined_multiplier = batch_multiplier * cache_multiplier
        combined_discount = 1 - combined_multiplier
        return int(combined_discount * 100)


class ProviderCapabilities:
    """
    Provider capability registry.

    Singleton pattern - maintains authoritative list of provider capabilities.
    Phase 1: Anthropic only. Phase 2+: Add OpenAI, Gemini, etc.
    """

    # Provider capability database (Phase 1: Anthropic only)
    _CAPABILITIES: dict[str, ProviderCapability] = {
        # Anthropic Claude - Full support
        LLMProvider.ANTHROPIC.value: ProviderCapability(
            provider=LLMProvider.ANTHROPIC.value,
            supports_batch=True,
            supports_caching=True,
            batch_max_size=10000,
            batch_discount_percent=50,  # 50% off for batch
            cache_discount_percent=90,  # 90% off for cached tokens
        ),
        # Phase 2: OpenAI
        # LLMProvider.OPENAI.value: ProviderCapability(
        #     provider=LLMProvider.OPENAI.value,
        #     supports_batch=True,
        #     supports_caching=True,  # Automatic caching
        #     batch_max_size=50000,
        #     batch_discount_percent=50,
        #     cache_discount_percent=50,  # Automatic caching ~50% effective
        #   ),
        # Phase 2: Google Gemini
        # LLMProvider.GEMINI.value: ProviderCapability(
        #     provider=LLMProvider.GEMINI.value,
        #     supports_batch=True,
        #     supports_caching=True,
        #     batch_max_size=1000,
        #     batch_discount_percent=50,
        #     cache_discount_percent=90,  # Context caching
        # ),
    }

    @classmethod
    def get(cls, provider: str) -> ProviderCapability:
        """
        Get capabilities for a provider.

        Args:
            provider: Provider identifier (e.g., "anthropic")

        Returns:
            ProviderCapability for the provider, or unsupported capability

        Example:
            >>> cap = ProviderCapabilities.get("anthropic")
            >>> cap.supports_batch
            True
            >>> cap.supports_caching
            True
            >>> cap.combined_discount_percent
            95
        """
        # Return known capability or create unsupported one
        return cls._CAPABILITIES.get(
            provider,
            ProviderCapability(
                provider=provider,
                supports_batch=False,
                supports_caching=False,
            ),
        )

    @classmethod
    def supports_batch(cls, provider: str) -> bool:
        """Check if provider supports Batch API."""
        return cls.get(provider).supports_batch

    @classmethod
    def supports_caching(cls, provider: str) -> bool:
        """Check if provider supports Prompt Caching."""
        return cls.get(provider).supports_caching

    @classmethod
    def supports_any_optimization(cls, provider: str) -> bool:
        """Check if provider supports any optimization."""
        cap = cls.get(provider)
        return cap.supports_batch or cap.supports_caching

    @classmethod
    def get_batch_max_size(cls, provider: str) -> Optional[int]:
        """Get maximum batch size for provider (None if unsupported)."""
        return cls.get(provider).batch_max_size

    @classmethod
    def list_supported_providers(cls) -> list[str]:
        """
        List all providers with optimization support.

        Returns:
            List of provider identifiers that support at least one optimization
        """
        return [
            provider
            for provider, cap in cls._CAPABILITIES.items()
            if cap.supports_batch or cap.supports_caching
        ]

    @classmethod
    def get_optimization_summary(cls, provider: str) -> dict:
        """
        Get human-readable optimization summary.

        Args:
            provider: Provider identifier

        Returns:
            Dictionary with capability summary

        Example:
            >>> summary = ProviderCapabilities.get_optimization_summary("anthropic")
            >>> summary["supports_batch"]
            True
            >>> summary["potential_savings"]
            "Up to 95% cost reduction"
        """
        cap = cls.get(provider)

        if not cap.supports_batch and not cap.supports_caching:
            return {
                "provider": provider,
                "supports_batch": False,
                "supports_caching": False,
                "potential_savings": "No optimizations available",
            }

        savings_desc = []
        if cap.supports_batch:
            savings_desc.append(f"{cap.batch_discount_percent}% via Batch API")
        if cap.supports_caching:
            savings_desc.append(f"{cap.cache_discount_percent}% via Caching")

        combined = cap.combined_discount_percent
        potential = f"Up to {combined}% cost reduction ({', '.join(savings_desc)})"

        return {
            "provider": provider,
            "supports_batch": cap.supports_batch,
            "supports_caching": cap.supports_caching,
            "batch_max_size": cap.batch_max_size,
            "batch_discount": f"{cap.batch_discount_percent}%",
            "cache_discount": f"{cap.cache_discount_percent}%",
            "combined_discount": f"{combined}%",
            "potential_savings": potential,
        }
