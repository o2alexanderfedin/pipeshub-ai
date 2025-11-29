"""
Custom exceptions for LLM optimization module.

Follows exception hierarchy:
    OptimizationError (base)
    ├── BatchAPIError (batch-related failures)
    ├── CacheError (cache-related failures)
    └── ConfigurationError (config validation failures)
"""

from typing import Optional


class OptimizationError(Exception):
    """Base exception for all LLM optimization errors."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> None:
        """
        Initialize optimization error.

        Args:
            message: Human-readable error description
            provider: Optional provider name (e.g., "anthropic")
            details: Optional additional error context
        """
        self.message = message
        self.provider = provider
        self.details = details or {}
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format error message with context."""
        msg = self.message
        if self.provider:
            msg = f"[{self.provider}] {msg}"
        if self.details:
            detail_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            msg = f"{msg} ({detail_str})"
        return msg


class BatchAPIError(OptimizationError):
    """Raised when batch API operations fail."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        batch_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> None:
        """
        Initialize batch API error.

        Args:
            message: Error description
            provider: Provider name
            batch_id: Optional batch job ID
            status: Optional batch status at failure
        """
        details = {}
        if batch_id:
            details["batch_id"] = batch_id
        if status:
            details["status"] = status
        super().__init__(message, provider, details)


class CacheError(OptimizationError):
    """Raised when prompt caching operations fail."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        cache_key: Optional[str] = None,
    ) -> None:
        """
        Initialize cache error.

        Args:
            message: Error description
            provider: Provider name
            cache_key: Optional cache key that failed
        """
        details = {}
        if cache_key:
            details["cache_key"] = cache_key
        super().__init__(message, provider, details)


class ConfigurationError(OptimizationError):
    """Raised when configuration validation fails."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[any] = None,
    ) -> None:
        """
        Initialize configuration error.

        Args:
            message: Error description
            field: Optional configuration field that failed validation
            value: Optional invalid value
        """
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        super().__init__(message, provider=None, details=details)
