"""
Unit tests for Anthropic Prompt Caching manager.

Tests cache marker injection, TTL handling, and auto-detection.
Target: 90%+ coverage, all message types tested.
"""

import pytest
from typing import Any

from app.utils.llm_optimization.cache_manager import (
    CacheManager,
    CacheableContent,
    CacheStats,
)
from app.utils.llm_optimization.config import CacheConfig
from app.utils.llm_optimization.exceptions import CacheError


class TestCacheableContent:
    """Test CacheableContent dataclass."""

    def test_create_cacheable_text(self) -> None:
        """Test creating cacheable text content."""
        content = CacheableContent(
            content_type="text",
            text="This is a long prompt that should be cached.",
            estimated_tokens=100,
            should_cache=True,
        )

        assert content.content_type == "text"
        assert content.text == "This is a long prompt that should be cached."
        assert content.estimated_tokens == 100
        assert content.should_cache is True

    def test_estimate_tokens_simple(self) -> None:
        """Test simple token estimation (4 chars per token)."""
        content = CacheableContent(
            content_type="text",
            text="Hello world",  # 11 chars ~= 3 tokens
        )

        assert content.estimated_tokens == 3  # 11 / 4 = 2.75 -> 3

    def test_estimate_tokens_long_text(self) -> None:
        """Test token estimation for longer text."""
        text = "This is a longer piece of text " * 100  # ~3200 chars
        content = CacheableContent(
            content_type="text",
            text=text,
        )

        assert content.estimated_tokens > 700  # Should be ~800 tokens


class TestCacheStats:
    """Test CacheStats dataclass."""

    def test_create_cache_stats(self) -> None:
        """Test creating cache statistics."""
        stats = CacheStats(
            total_content_blocks=10,
            cached_blocks=5,
            estimated_cached_tokens=5000,
            cache_hit_potential=0.5,
        )

        assert stats.total_content_blocks == 10
        assert stats.cached_blocks == 5
        assert stats.estimated_cached_tokens == 5000
        assert stats.cache_hit_potential == 0.5


class TestCacheManager:
    """Test CacheManager class."""

    @pytest.fixture
    def cache_config(self) -> CacheConfig:
        """Create cache configuration for testing."""
        return CacheConfig(
            enabled=True,
            default_ttl_seconds=300,  # 5 minutes
            domain_definitions_ttl_seconds=3600,  # 1 hour
            min_tokens_to_cache=1024,
            auto_detect_cacheable=True,
        )

    @pytest.fixture
    def cache_manager(self, cache_config: CacheConfig) -> CacheManager:
        """Create CacheManager for testing."""
        return CacheManager(config=cache_config)

    def test_create_manager(self, cache_config: CacheConfig) -> None:
        """Test creating CacheManager."""
        manager = CacheManager(config=cache_config)
        assert manager.config == cache_config

    def test_inject_cache_markers_disabled(self) -> None:
        """Test that cache markers are not injected when disabled."""
        config = CacheConfig(enabled=False)
        manager = CacheManager(config=config)

        messages = [
            {"role": "user", "content": "Hello world"}
        ]

        result = manager.inject_cache_markers(messages)
        assert result == messages  # No modification

    def test_inject_cache_system_message(self, cache_manager: CacheManager) -> None:
        """Test injecting cache marker into system message."""
        long_text = "System instructions. " * 100  # ~2100 chars = ~525 tokens (below threshold)
        very_long_text = "System instructions. " * 250  # ~5250 chars = ~1312 tokens (above threshold)

        messages = [
            {"role": "system", "content": very_long_text},
            {"role": "user", "content": "What is the weather?"},
        ]

        result = cache_manager.inject_cache_markers(messages)

        # System message should have cache_control
        assert "cache_control" in result[0]
        assert result[0]["cache_control"]["type"] == "ephemeral"
        assert result[0]["content"] == very_long_text

    def test_inject_cache_user_message_text(self, cache_manager: CacheManager) -> None:
        """Test injecting cache marker into user text message."""
        long_text = "User query with context. " * 250  # ~6500 chars = ~1625 tokens

        messages = [
            {"role": "user", "content": long_text},
        ]

        result = cache_manager.inject_cache_markers(messages)

        # User message should have cache_control
        assert "cache_control" in result[0]
        assert result[0]["cache_control"]["type"] == "ephemeral"

    def test_inject_cache_user_message_blocks(self, cache_manager: CacheManager) -> None:
        """Test injecting cache marker into user message with content blocks."""
        long_text = "Context information. " * 250  # ~5250 chars = ~1312 tokens

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": long_text},
                    {"type": "text", "text": "What is your analysis?"},
                ],
            }
        ]

        result = cache_manager.inject_cache_markers(messages)

        # First content block should have cache_control
        assert "cache_control" in result[0]["content"][0]
        assert result[0]["content"][0]["cache_control"]["type"] == "ephemeral"
        # Second block should not
        assert "cache_control" not in result[0]["content"][1]

    def test_no_cache_below_threshold(self, cache_manager: CacheManager) -> None:
        """Test that content below token threshold is not cached."""
        short_text = "Short message"  # ~13 chars = ~3 tokens

        messages = [
            {"role": "user", "content": short_text},
        ]

        result = cache_manager.inject_cache_markers(messages)

        # Should not have cache_control (below threshold)
        assert "cache_control" not in result[0]

    def test_cache_multiple_messages_last_only(self, cache_manager: CacheManager) -> None:
        """Test that only last cacheable message gets cache marker."""
        long_text1 = "First long context. " * 250  # Above threshold
        long_text2 = "Second long context. " * 250  # Above threshold

        messages = [
            {"role": "user", "content": long_text1},
            {"role": "assistant", "content": "Response"},
            {"role": "user", "content": long_text2},
        ]

        result = cache_manager.inject_cache_markers(messages)

        # Only the last user message should have cache_control
        assert "cache_control" not in result[0]
        assert "cache_control" in result[2]

    def test_cache_domain_definitions(self, cache_manager: CacheManager) -> None:
        """Test caching domain definitions with longer TTL."""
        domain_text = "Domain definitions: " * 250  # Above threshold

        # Mark as domain definitions
        messages = [
            {
                "role": "system",
                "content": domain_text,
                "metadata": {"content_type": "domain_definitions"},
            },
            {"role": "user", "content": "User query"},
        ]

        result = cache_manager.inject_cache_markers(messages)

        # System message should be cached
        assert "cache_control" in result[0]
        # Note: TTL is configured in config, not in the cache_control marker

    def test_auto_detect_disabled(self) -> None:
        """Test that auto-detection can be disabled."""
        config = CacheConfig(
            enabled=True,
            auto_detect_cacheable=False,
            min_tokens_to_cache=1024,
        )
        manager = CacheManager(config=config)

        long_text = "Long text. " * 250  # Above threshold

        messages = [
            {"role": "user", "content": long_text},
        ]

        result = manager.inject_cache_markers(messages)

        # Should not auto-detect, no cache markers
        assert "cache_control" not in result[0]

    def test_explicit_cache_markers(self, cache_manager: CacheManager) -> None:
        """Test that explicit cache markers are preserved."""
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Cached content",
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
            }
        ]

        result = cache_manager.inject_cache_markers(messages)

        # Explicit marker should be preserved
        assert result[0]["content"][0]["cache_control"]["type"] == "ephemeral"

    def test_get_cache_stats(self, cache_manager: CacheManager) -> None:
        """Test getting cache statistics."""
        long_text = "Context. " * 250  # ~2250 chars = ~562 tokens

        messages = [
            {"role": "system", "content": long_text},
            {"role": "user", "content": long_text},
        ]

        cache_manager.inject_cache_markers(messages)
        stats = cache_manager.get_cache_stats()

        assert stats.total_content_blocks > 0
        # Stats depend on whether content was cached

    def test_estimate_tokens_accurate(self, cache_manager: CacheManager) -> None:
        """Test token estimation accuracy."""
        # Test with known text
        text = "Hello, world! " * 100  # 1400 chars

        tokens = cache_manager.estimate_tokens(text)

        # Should be ~350 tokens (1400 / 4)
        assert 300 <= tokens <= 400

    def test_is_cacheable_threshold(self, cache_manager: CacheManager) -> None:
        """Test cacheability threshold detection."""
        # Below threshold
        short_text = "Short"  # ~1 token
        assert cache_manager.is_cacheable(short_text) is False

        # Above threshold
        long_text = "x" * 5000  # ~1250 tokens
        assert cache_manager.is_cacheable(long_text) is True

    def test_preserve_message_structure(self, cache_manager: CacheManager) -> None:
        """Test that message structure is preserved."""
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Query"},
                    {"type": "image", "source": {"type": "url", "url": "https://example.com/img.jpg"}},
                ],
                "metadata": {"custom": "data"},
            }
        ]

        result = cache_manager.inject_cache_markers(messages)

        # Structure should be preserved
        assert result[0]["role"] == "user"
        assert result[0]["metadata"]["custom"] == "data"
        assert len(result[0]["content"]) == 2
        assert result[0]["content"][1]["type"] == "image"

    def test_handle_complex_content_blocks(self, cache_manager: CacheManager) -> None:
        """Test handling various content block types."""
        long_text = "Analysis context. " * 250

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": long_text},
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": "..."}},
                    {"type": "text", "text": "What do you see?"},
                ],
            }
        ]

        result = cache_manager.inject_cache_markers(messages)

        # First text block should be cached
        assert result[0]["content"][0]["cache_control"]["type"] == "ephemeral"
        # Image should be preserved
        assert result[0]["content"][1]["type"] == "image"
        # Last text should not be cached
        assert "cache_control" not in result[0]["content"][2]

    def test_cache_error_invalid_message(self, cache_manager: CacheManager) -> None:
        """Test error handling for invalid messages."""
        invalid_messages = [
            {"invalid": "structure"},
        ]

        # Should handle gracefully or raise CacheError
        # Depending on implementation, either:
        # 1. Return original messages unchanged
        # 2. Raise CacheError
        try:
            result = cache_manager.inject_cache_markers(invalid_messages)
            # If no error, should return original
            assert result == invalid_messages
        except CacheError:
            # Expected behavior
            pass

    def test_reset_stats(self, cache_manager: CacheManager) -> None:
        """Test resetting cache statistics."""
        long_text = "Text. " * 250

        messages = [{"role": "user", "content": long_text}]
        cache_manager.inject_cache_markers(messages)

        # Reset stats
        cache_manager.reset_stats()
        stats = cache_manager.get_cache_stats()

        assert stats.total_content_blocks == 0
        assert stats.cached_blocks == 0

    def test_config_validation(self) -> None:
        """Test configuration validation."""
        # Valid config
        config = CacheConfig(
            enabled=True,
            min_tokens_to_cache=256,
        )
        manager = CacheManager(config=config)
        assert manager.config.min_tokens_to_cache == 256

    def test_cache_only_text_blocks(self, cache_manager: CacheManager) -> None:
        """Test that only text content blocks are cached, not images."""
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "url", "url": "https://example.com/large.jpg"}},
                ],
            }
        ]

        result = cache_manager.inject_cache_markers(messages)

        # Image should not have cache_control
        assert "cache_control" not in result[0]["content"][0]

    def test_multiple_system_messages(self, cache_manager: CacheManager) -> None:
        """Test handling multiple system messages."""
        long_text = "Instructions. " * 300  # 4200 chars = 1050 tokens (above threshold)

        messages = [
            {"role": "system", "content": long_text},
            {"role": "system", "content": long_text},
            {"role": "user", "content": "Query"},
        ]

        result = cache_manager.inject_cache_markers(messages)

        # Only last system message should be cached
        assert "cache_control" not in result[0]
        assert "cache_control" in result[1]
