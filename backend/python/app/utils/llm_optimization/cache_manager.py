"""
Anthropic Prompt Caching manager for LLM optimization.

Handles cache marker injection, token estimation, and cache statistics.
Supports up to 90% cost reduction for cached content.
"""

import copy
import math
from dataclasses import dataclass, field
from typing import Any, Optional

from app.utils.llm_optimization.config import CacheConfig
from app.utils.llm_optimization.exceptions import CacheError


@dataclass
class CacheableContent:
    """
    Cacheable content with token estimation.

    Attributes:
        content_type: Type of content ("text", "image", etc.)
        text: Text content (for text type)
        estimated_tokens: Estimated token count
        should_cache: Whether content should be cached
    """

    content_type: str
    text: Optional[str] = None
    estimated_tokens: int = 0
    should_cache: bool = False

    def __post_init__(self) -> None:
        """Estimate tokens if not provided."""
        if self.estimated_tokens == 0 and self.text:
            # Simple estimation: ~4 characters per token (round up)
            self.estimated_tokens = math.ceil(len(self.text) / 4)


@dataclass
class CacheStats:
    """
    Cache statistics for monitoring and optimization.

    Attributes:
        total_content_blocks: Total number of content blocks processed
        cached_blocks: Number of blocks marked for caching
        estimated_cached_tokens: Estimated tokens in cached content
        cache_hit_potential: Estimated cache hit rate (0.0-1.0)
    """

    total_content_blocks: int = 0
    cached_blocks: int = 0
    estimated_cached_tokens: int = 0
    cache_hit_potential: float = 0.0


class CacheManager:
    """
    Anthropic Prompt Caching manager.

    Handles injection of cache_control markers into messages to enable
    prompt caching with configurable TTL and auto-detection.

    Best practices:
    - Cache only static/repeated content (system prompts, domain definitions)
    - Only last cache_control marker in sequence is used
    - Minimum 1024 tokens recommended for cost benefit
    - 90% cost reduction for cached tokens
    """

    def __init__(self, config: CacheConfig) -> None:
        """
        Initialize Cache Manager.

        Args:
            config: Cache configuration
        """
        self.config = config
        self._stats = CacheStats()

    def inject_cache_markers(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Inject cache_control markers into messages.

        Args:
            messages: List of message dictionaries

        Returns:
            Modified messages with cache markers (if enabled)

        Note:
            - Only modifies messages if caching is enabled
            - Preserves original message structure
            - Caches only the last cacheable message (Anthropic best practice)
        """
        if not self.config.enabled:
            return messages

        # Deep copy to avoid modifying original
        messages = copy.deepcopy(messages)

        # Track cacheable positions
        cacheable_positions: list[tuple[int, Optional[int]]] = []

        for msg_idx, message in enumerate(messages):
            if not isinstance(message, dict) or "role" not in message:
                continue

            role = message.get("role")
            content = message.get("content")

            if not content:
                continue

            # Handle string content
            if isinstance(content, str):
                self._stats.total_content_blocks += 1
                if self._should_cache_content(content, message):
                    cacheable_positions.append((msg_idx, None))

            # Handle content blocks
            elif isinstance(content, list):
                for block_idx, block in enumerate(content):
                    if not isinstance(block, dict):
                        continue

                    self._stats.total_content_blocks += 1

                    # Check if block already has cache_control
                    if "cache_control" in block:
                        cacheable_positions.append((msg_idx, block_idx))
                        continue

                    # Only cache text blocks
                    if block.get("type") == "text":
                        text = block.get("text", "")
                        if self._should_cache_content(text, message):
                            cacheable_positions.append((msg_idx, block_idx))

        # Apply cache marker only to last cacheable position
        if cacheable_positions:
            msg_idx, block_idx = cacheable_positions[-1]

            if block_idx is None:
                # String content
                messages[msg_idx]["cache_control"] = {"type": "ephemeral"}
            else:
                # Content block
                if "cache_control" not in messages[msg_idx]["content"][block_idx]:
                    messages[msg_idx]["content"][block_idx]["cache_control"] = {"type": "ephemeral"}

            self._stats.cached_blocks += 1

            # Estimate cached tokens
            if block_idx is None:
                content_text = messages[msg_idx]["content"]
                if isinstance(content_text, str):
                    self._stats.estimated_cached_tokens += self.estimate_tokens(content_text)
            else:
                block = messages[msg_idx]["content"][block_idx]
                if block.get("type") == "text":
                    self._stats.estimated_cached_tokens += self.estimate_tokens(block.get("text", ""))

        # Update cache hit potential
        if self._stats.total_content_blocks > 0:
            self._stats.cache_hit_potential = self._stats.cached_blocks / self._stats.total_content_blocks

        return messages

    def _should_cache_content(self, content: str, message: dict[str, Any]) -> bool:
        """
        Determine if content should be cached.

        Args:
            content: Text content to evaluate
            message: Full message context

        Returns:
            True if content should be cached
        """
        # Auto-detection must be enabled
        if not self.config.auto_detect_cacheable:
            return False

        # Check token threshold
        if not self.is_cacheable(content):
            return False

        return True

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Uses simple heuristic: ~4 characters per token.
        This is approximate; actual tokenization may vary.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        if not text:
            return 0

        # Simple estimation: 4 chars per token (round up)
        return math.ceil(len(text) / 4)

    def is_cacheable(self, text: str) -> bool:
        """
        Check if text meets minimum token threshold for caching.

        Args:
            text: Text to evaluate

        Returns:
            True if text has enough tokens to benefit from caching
        """
        estimated_tokens = self.estimate_tokens(text)
        return estimated_tokens >= self.config.min_tokens_to_cache

    def get_cache_stats(self) -> CacheStats:
        """
        Get current cache statistics.

        Returns:
            CacheStats with current metrics
        """
        return copy.copy(self._stats)

    def reset_stats(self) -> None:
        """Reset cache statistics."""
        self._stats = CacheStats()

    def get_ttl_for_content_type(self, content_type: str) -> int:
        """
        Get TTL (time-to-live) for content type.

        Args:
            content_type: Type of content (e.g., "domain_definitions")

        Returns:
            TTL in seconds
        """
        if content_type == "domain_definitions":
            return self.config.domain_definitions_ttl_seconds
        return self.config.default_ttl_seconds
