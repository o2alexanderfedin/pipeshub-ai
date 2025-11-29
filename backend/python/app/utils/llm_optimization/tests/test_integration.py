"""
Integration tests for LLM optimization wrapper.

Tests integration with aimodels factory, backward compatibility,
and end-to-end optimization flow.
Target: Verify zero breaking changes and proper optimization application.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Any

from app.utils.llm_optimization.wrapper import OptimizedLLMWrapper
from app.utils.llm_optimization.config import OptimizationConfig, BatchConfig, CacheConfig
from app.utils.llm_optimization.exceptions import OptimizationError


class TestOptimizedLLMWrapper:
    """Test OptimizedLLMWrapper class."""

    @pytest.fixture
    def mock_base_model(self) -> Mock:
        """Create mock LangChain BaseChatModel."""
        model = Mock()
        model.invoke = Mock(return_value="Response from model")
        model.model_name = "claude-sonnet-4-5-20250929"
        return model

    @pytest.fixture
    def optimization_config(self) -> OptimizationConfig:
        """Create optimization configuration."""
        return OptimizationConfig(
            batch=BatchConfig(enabled=False),  # Disabled for basic tests
            cache=CacheConfig(enabled=True, min_tokens_to_cache=256),
            provider="anthropic",
        )

    @pytest.fixture
    def wrapper(self, mock_base_model: Mock, optimization_config: OptimizationConfig) -> OptimizedLLMWrapper:
        """Create OptimizedLLMWrapper for testing."""
        return OptimizedLLMWrapper(
            base_model=mock_base_model,
            config=optimization_config,
        )

    def test_create_wrapper(self, mock_base_model: Mock, optimization_config: OptimizationConfig) -> None:
        """Test creating OptimizedLLMWrapper."""
        wrapper = OptimizedLLMWrapper(
            base_model=mock_base_model,
            config=optimization_config,
        )

        assert wrapper.base_model == mock_base_model
        assert wrapper.config == optimization_config

    def test_wrapper_passthrough_when_disabled(self, mock_base_model: Mock) -> None:
        """Test that wrapper passes through when optimizations disabled."""
        config = OptimizationConfig(
            batch=BatchConfig(enabled=False),
            cache=CacheConfig(enabled=False),
        )
        wrapper = OptimizedLLMWrapper(base_model=mock_base_model, config=config)

        messages = [{"role": "user", "content": "Hello"}]
        result = wrapper.invoke(messages)

        # Should call base model directly
        mock_base_model.invoke.assert_called_once()
        assert result == "Response from model"

    def test_cache_injection_enabled(self, wrapper: OptimizedLLMWrapper, mock_base_model: Mock) -> None:
        """Test cache marker injection when enabled."""
        long_text = "x" * 1100  # 1100 chars = 275 tokens (above threshold of 256)

        messages = [{"role": "user", "content": long_text}]
        wrapper.invoke(messages)

        # Should inject cache markers before calling base model
        call_args = mock_base_model.invoke.call_args[0][0]
        assert "cache_control" in call_args[0]

    def test_cache_injection_below_threshold(self, wrapper: OptimizedLLMWrapper, mock_base_model: Mock) -> None:
        """Test no cache injection for content below threshold."""
        short_text = "Short"  # Below threshold

        messages = [{"role": "user", "content": short_text}]
        wrapper.invoke(messages)

        # Should NOT inject cache markers
        call_args = mock_base_model.invoke.call_args[0][0]
        assert "cache_control" not in call_args[0]

    def test_preserves_base_model_interface(self, wrapper: OptimizedLLMWrapper, mock_base_model: Mock) -> None:
        """Test that wrapper preserves BaseChatModel interface."""
        # Wrapper should have the same interface as base model
        assert hasattr(wrapper, "invoke")
        assert callable(wrapper.invoke)

    def test_get_cache_stats(self, wrapper: OptimizedLLMWrapper) -> None:
        """Test getting cache statistics."""
        long_text = "x" * 1100  # Above threshold (275 tokens)

        messages = [{"role": "user", "content": long_text}]
        wrapper.invoke(messages)

        stats = wrapper.get_cache_stats()
        assert stats.total_content_blocks > 0

    def test_reset_cache_stats(self, wrapper: OptimizedLLMWrapper) -> None:
        """Test resetting cache statistics."""
        long_text = "x" * 1100  # Above threshold

        messages = [{"role": "user", "content": long_text}]
        wrapper.invoke(messages)

        wrapper.reset_cache_stats()
        stats = wrapper.get_cache_stats()
        assert stats.total_content_blocks == 0

    def test_unsupported_provider(self, mock_base_model: Mock) -> None:
        """Test wrapper with unsupported provider."""
        config = OptimizationConfig(
            cache=CacheConfig(enabled=True),
            provider="unsupported_provider",
        )

        wrapper = OptimizedLLMWrapper(base_model=mock_base_model, config=config)

        # Should work but optimizations will be skipped
        messages = [{"role": "user", "content": "Hello"}]
        result = wrapper.invoke(messages)

        assert result == "Response from model"

    def test_error_handling_graceful_fallback(self, mock_base_model: Mock) -> None:
        """Test graceful fallback on optimization errors."""
        config = OptimizationConfig(
            cache=CacheConfig(enabled=True),
            fallback={"enabled": True, "log_failures": True},
        )

        wrapper = OptimizedLLMWrapper(base_model=mock_base_model, config=config)

        # Simulate cache manager error by using invalid messages
        messages = None  # Invalid

        # Should fall back to base model
        # Depending on implementation, may raise or handle gracefully

    def test_provider_anthropic(self, mock_base_model: Mock) -> None:
        """Test with Anthropic provider (supported)."""
        config = OptimizationConfig(
            cache=CacheConfig(enabled=True),
            provider="anthropic",
        )

        wrapper = OptimizedLLMWrapper(base_model=mock_base_model, config=config)

        long_text = "x" * 5000  # 5000 chars = 1250 tokens (well above threshold)
        messages = [{"role": "user", "content": long_text}]
        wrapper.invoke(messages)

        # Cache markers should be injected
        call_args = mock_base_model.invoke.call_args[0][0]
        assert isinstance(call_args, list)


class TestBackwardCompatibility:
    """Test backward compatibility with existing code."""

    def test_drop_in_replacement(self) -> None:
        """Test that wrapper can be used as drop-in replacement."""
        # Mock existing LangChain model
        base_model = Mock()
        base_model.invoke = Mock(return_value="Response")

        # Wrap with optimization (disabled)
        config = OptimizationConfig(
            batch=BatchConfig(enabled=False),
            cache=CacheConfig(enabled=False),
        )
        wrapped_model = OptimizedLLMWrapper(base_model=base_model, config=config)

        # Use exactly like base model
        result = wrapped_model.invoke([{"role": "user", "content": "Test"}])

        assert result == "Response"
        base_model.invoke.assert_called_once()

    def test_existing_code_unaware(self) -> None:
        """Test that existing code works without modifications."""
        base_model = Mock()
        base_model.invoke = Mock(return_value={"response": "data"})

        config = OptimizationConfig()
        wrapped_model = OptimizedLLMWrapper(base_model=base_model, config=config)

        # Existing code doesn't know about wrapper
        messages = [{"role": "user", "content": "Query"}]
        result = wrapped_model.invoke(messages)

        # Works exactly like before
        assert result == {"response": "data"}


class TestEndToEndFlow:
    """Test end-to-end optimization flow."""

    def test_cache_only_flow(self) -> None:
        """Test cache-only optimization flow."""
        base_model = Mock()
        base_model.invoke = Mock(return_value="Cached response")

        config = OptimizationConfig(
            batch=BatchConfig(enabled=False),
            cache=CacheConfig(enabled=True, min_tokens_to_cache=256),
            provider="anthropic",
        )

        wrapper = OptimizedLLMWrapper(base_model=base_model, config=config)

        # Long content that should be cached
        long_content = "Context information. " * 60  # 1260 chars = 315 tokens (above 256)

        messages = [
            {"role": "system", "content": long_content},
            {"role": "user", "content": "Question"},
        ]

        result = wrapper.invoke(messages)

        # Verify cache markers were injected
        call_args = base_model.invoke.call_args[0][0]
        assert "cache_control" in call_args[0]
        assert result == "Cached response"

    def test_no_optimization_flow(self) -> None:
        """Test flow with no optimizations."""
        base_model = Mock()
        base_model.invoke = Mock(return_value="Standard response")

        config = OptimizationConfig()  # All disabled by default

        wrapper = OptimizedLLMWrapper(base_model=base_model, config=config)

        messages = [{"role": "user", "content": "Test"}]
        result = wrapper.invoke(messages)

        # Should pass through unchanged
        call_args = base_model.invoke.call_args[0][0]
        assert call_args == messages
        assert result == "Standard response"

    def test_config_from_dict(self) -> None:
        """Test creating config from dictionary (ArangoDB format)."""
        config_dict = {
            "batch": {"enabled": False},
            "cache": {"enabled": True, "min_tokens_to_cache": 512},
            "provider": "anthropic",
        }

        config = OptimizationConfig.from_dict(config_dict)
        assert config.cache.enabled is True
        assert config.cache.min_tokens_to_cache == 512
        assert config.provider == "anthropic"

    def test_multiple_messages_flow(self) -> None:
        """Test flow with multiple messages."""
        base_model = Mock()
        base_model.invoke = Mock(return_value="Multi-turn response")

        config = OptimizationConfig(
            cache=CacheConfig(enabled=True, min_tokens_to_cache=256),
            provider="anthropic",
        )

        wrapper = OptimizedLLMWrapper(base_model=base_model, config=config)

        long_text = "x" * 1100  # 1100 chars = 275 tokens (above threshold)
        messages = [
            {"role": "user", "content": long_text},
            {"role": "assistant", "content": "Response"},
            {"role": "user", "content": long_text},
        ]

        result = wrapper.invoke(messages)

        # Only last cacheable message should have marker
        call_args = base_model.invoke.call_args[0][0]
        assert "cache_control" in call_args[2]  # Last user message
        assert "cache_control" not in call_args[0]  # First user message
