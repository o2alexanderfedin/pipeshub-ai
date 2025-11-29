"""
Configuration models for LLM optimization.

Uses Pydantic for strong typing and validation.
All fields have safe defaults to ensure backward compatibility.
"""

from typing import Any, Optional, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict


class BatchConfig(BaseModel):
    """Configuration for Batch API optimization."""

    enabled: bool = Field(
        default=False,
        description="Enable batch API optimization (disabled by default for safety)",
    )
    max_batch_size: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Maximum number of requests per batch (1-10000)",
    )
    timeout_seconds: int = Field(
        default=86400,  # 24 hours
        ge=60,
        le=259200,  # 72 hours max
        description="Batch processing timeout in seconds",
    )
    accumulation_strategy: Literal["time", "count", "hybrid"] = Field(
        default="hybrid",
        description="Batch accumulation strategy: time-based, count-based, or hybrid",
    )
    accumulation_time_seconds: int = Field(
        default=30,
        ge=1,
        le=300,  # 5 minutes max
        description="Time to wait before submitting batch (for time/hybrid strategies)",
    )
    retry_attempts: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Number of retry attempts for failed batch items",
    )

    @field_validator("max_batch_size")
    @classmethod
    def validate_batch_size(cls, v: int) -> int:
        """Ensure batch size is reasonable."""
        if v > 10000:
            raise ValueError("Batch size cannot exceed 10,000 (provider limit)")
        return v


class CacheConfig(BaseModel):
    """Configuration for Prompt Caching optimization."""

    enabled: bool = Field(
        default=False,
        description="Enable prompt caching optimization (disabled by default for safety)",
    )
    default_ttl_seconds: int = Field(
        default=300,  # 5 minutes
        ge=60,
        le=3600,  # 1 hour max for Phase 1
        description="Default cache TTL in seconds",
    )
    domain_definitions_ttl_seconds: int = Field(
        default=3600,  # 1 hour
        ge=300,
        le=86400,  # 24 hours max
        description="Cache TTL for domain definitions (typically longer-lived)",
    )
    min_tokens_to_cache: int = Field(
        default=1024,
        ge=256,
        description="Minimum tokens required to benefit from caching",
    )
    auto_detect_cacheable: bool = Field(
        default=True,
        description="Automatically detect cacheable content based on heuristics",
    )

    @field_validator("default_ttl_seconds", "domain_definitions_ttl_seconds")
    @classmethod
    def validate_ttl(cls, v: int) -> int:
        """Ensure TTL is within reasonable bounds."""
        if v < 60:
            raise ValueError("TTL must be at least 60 seconds")
        if v > 86400:
            raise ValueError("TTL cannot exceed 24 hours in Phase 1")
        return v


class FallbackConfig(BaseModel):
    """Configuration for fallback behavior when optimization fails."""

    enabled: bool = Field(
        default=True,
        description="Enable graceful fallback to standard API on errors",
    )
    log_failures: bool = Field(
        default=True,
        description="Log optimization failures for debugging",
    )
    raise_on_fallback: bool = Field(
        default=False,
        description="Raise exception on fallback (useful for testing)",
    )


class OptimizationConfig(BaseModel):
    """
    Complete optimization configuration.

    All optimizations disabled by default for zero production impact.
    Enable selectively after testing in dev environment.
    """

    batch: BatchConfig = Field(
        default_factory=BatchConfig,
        description="Batch API configuration",
    )
    cache: CacheConfig = Field(
        default_factory=CacheConfig,
        description="Prompt caching configuration",
    )
    fallback: FallbackConfig = Field(
        default_factory=FallbackConfig,
        description="Fallback behavior configuration",
    )
    provider: Optional[str] = Field(
        default=None,
        description="Provider name (e.g., 'anthropic', 'openai')",
    )

    @property
    def is_any_optimization_enabled(self) -> bool:
        """Check if any optimization is enabled."""
        return self.batch.enabled or self.cache.enabled

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OptimizationConfig":
        """
        Create config from dictionary (typically from ArangoDB).

        Args:
            data: Configuration dictionary

        Returns:
            OptimizationConfig instance with validated fields

        Raises:
            ConfigurationError: If validation fails
        """
        from app.utils.llm_optimization.exceptions import ConfigurationError

        try:
            return cls(**data)
        except Exception as e:
            raise ConfigurationError(
                message=f"Invalid optimization configuration: {str(e)}",
                field=getattr(e, "field", None),
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary for storage."""
        return self.dict(exclude_none=True)

    model_config = ConfigDict(
        validate_assignment=True,  # Validate on field updates
        extra="forbid",  # Reject unknown fields
    )
