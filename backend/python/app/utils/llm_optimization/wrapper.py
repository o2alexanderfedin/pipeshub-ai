"""
Optimized LLM wrapper for transparent cost optimization.

Wraps LangChain BaseChatModel instances with Batch API and Prompt Caching
optimizations while maintaining full backward compatibility.
"""

from typing import Any, Optional
from langchain.chat_models.base import BaseChatModel

from app.utils.llm_optimization.config import OptimizationConfig
from app.utils.llm_optimization.cache_manager import CacheManager, CacheStats
from app.utils.llm_optimization.capabilities import ProviderCapabilities
from app.utils.llm_optimization.exceptions import OptimizationError
from app.utils.logger import create_logger


logger = create_logger("llm_optimization.wrapper")


class OptimizedLLMWrapper:
    """
    Wrapper for LangChain BaseChatModel with cost optimizations.

    Transparently applies Batch API and Prompt Caching optimizations
    based on configuration without changing the external interface.

    Phase 1: Prompt Caching only (Batch API in Phase 2+)

    Example:
        >>> from app.utils.aimodels import get_generator_model
        >>> from app.utils.llm_optimization.wrapper import OptimizedLLMWrapper
        >>> from app.utils.llm_optimization.config import OptimizationConfig
        >>>
        >>> base_model = get_generator_model("anthropic", config)
        >>> config = OptimizationConfig(cache={"enabled": True})
        >>> model = OptimizedLLMWrapper(base_model, config)
        >>> # Use model exactly like base_model
        >>> response = model.invoke([{"role": "user", "content": "Hello"}])
    """

    def __init__(
        self,
        base_model: BaseChatModel,
        config: OptimizationConfig,
    ) -> None:
        """
        Initialize OptimizedLLMWrapper.

        Args:
            base_model: LangChain BaseChatModel to wrap
            config: Optimization configuration

        Note:
            Wrapper is transparent - callers use it exactly like base_model
        """
        self.base_model = base_model
        self.config = config

        # Initialize cache manager if caching enabled
        self._cache_manager: Optional[CacheManager] = None
        if self.config.cache.enabled:
            # Check if provider supports caching
            provider = self.config.provider or self._detect_provider()
            if ProviderCapabilities.supports_caching(provider):
                self._cache_manager = CacheManager(config=self.config.cache)
                logger.info(f"Cache optimization enabled for provider: {provider}")
            else:
                logger.warning(f"Cache optimization requested but not supported by provider: {provider}")

    def invoke(self, messages: list[dict[str, Any]], **kwargs: Any) -> Any:
        """
        Invoke the LLM with optimizations applied.

        Args:
            messages: List of message dictionaries
            **kwargs: Additional arguments passed to base model

        Returns:
            Model response (same as base_model.invoke)

        Note:
            - Applies cache markers if caching enabled
            - Falls back gracefully on errors
            - Transparent to caller
        """
        # Apply optimizations if enabled
        optimized_messages = messages

        try:
            # Apply cache optimization
            if self._cache_manager:
                optimized_messages = self._cache_manager.inject_cache_markers(messages)
                logger.debug(f"Cache markers injected for {len(messages)} messages")

        except Exception as e:
            # Graceful fallback on optimization errors
            if self.config.fallback.enabled:
                if self.config.fallback.log_failures:
                    logger.warning(f"Cache optimization failed, falling back to standard API: {e}")
                optimized_messages = messages
            else:
                raise OptimizationError(
                    message=f"Optimization failed: {str(e)}",
                    provider=self.config.provider,
                ) from e

        # Invoke base model with optimized messages
        return self.base_model.invoke(optimized_messages, **kwargs)

    def get_cache_stats(self) -> CacheStats:
        """
        Get cache statistics.

        Returns:
            CacheStats with current metrics

        Raises:
            OptimizationError: If caching not enabled
        """
        if not self._cache_manager:
            return CacheStats()  # Return empty stats

        return self._cache_manager.get_cache_stats()

    def reset_cache_stats(self) -> None:
        """Reset cache statistics."""
        if self._cache_manager:
            self._cache_manager.reset_stats()

    def _detect_provider(self) -> str:
        """
        Detect provider from base model.

        Returns:
            Provider identifier (e.g., "anthropic", "openai")

        Note:
            Best-effort detection based on model class name
        """
        model_class = type(self.base_model).__name__.lower()

        if "anthropic" in model_class:
            return "anthropic"
        elif "openai" in model_class:
            return "openai"
        elif "bedrock" in model_class:
            return "bedrock"
        elif "gemini" in model_class or "google" in model_class:
            return "gemini"
        elif "cohere" in model_class:
            return "cohere"
        else:
            logger.warning(f"Could not detect provider from model class: {model_class}")
            return "unknown"

    @property
    def is_optimized(self) -> bool:
        """Check if any optimization is active."""
        return self._cache_manager is not None

    def __repr__(self) -> str:
        """String representation."""
        optimizations = []
        if self._cache_manager:
            optimizations.append("cache")

        opt_str = ", ".join(optimizations) if optimizations else "none"
        return f"OptimizedLLMWrapper(base={type(self.base_model).__name__}, optimizations=[{opt_str}])"
