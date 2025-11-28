"""
Simple caching layer for Hupyy verification results.

Uses Redis with TTL (Time-To-Live) for temporary storage.
Supports:
- Chunk-level caching (hash-based keys)
- TTL configuration
- Cache hit/miss metrics
- LRU eviction (handled by Redis)
"""

import hashlib
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from redis import asyncio as aioredis


@dataclass
class CacheEntry:
    """Cache entry for verification results."""

    chunk_hash: str
    result: Dict[str, Any]
    ttl_seconds: int = 86400  # 24 hours default


class VerificationCache:
    """
    Cache for Hupyy verification results.

    Uses content-based hashing to identify unique chunks.
    """

    CACHE_PREFIX = "hupyy_verification:"

    def __init__(
        self,
        redis_client: aioredis.Redis,
        default_ttl: int = 86400,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """
        Initialize verification cache.

        Args:
            redis_client: Redis client instance
            default_ttl: Default TTL in seconds (24 hours)
            logger: Optional logger instance
        """
        self.redis_client = redis_client
        self.default_ttl = default_ttl
        self.logger = logger or logging.getLogger(__name__)

    @classmethod
    async def create(
        cls, redis_url: str, default_ttl: int = 86400, logger: Optional[logging.Logger] = None
    ) -> "VerificationCache":
        """
        Create VerificationCache instance.

        Args:
            redis_url: Redis connection URL
            default_ttl: Default TTL in seconds
            logger: Optional logger instance

        Returns:
            Initialized VerificationCache
        """
        redis_client = await aioredis.from_url(redis_url, encoding="utf-8", decode_responses=True)

        # Test connection
        await redis_client.ping()
        if logger:
            logger.info("✅ Connected to Redis for verification cache")

        return cls(redis_client, default_ttl, logger)

    def _compute_chunk_hash(self, content: str) -> str:
        """
        Compute hash for chunk content.

        Args:
            content: Chunk text content

        Returns:
            SHA256 hash of content
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _make_cache_key(self, chunk_hash: str) -> str:
        """
        Generate Redis key for chunk hash.

        Args:
            chunk_hash: Hash of chunk content

        Returns:
            Prefixed cache key
        """
        return f"{self.CACHE_PREFIX}{chunk_hash}"

    async def get(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Get verification result from cache.

        Args:
            content: Chunk content to look up

        Returns:
            Cached verification result or None if not found
        """
        try:
            chunk_hash = self._compute_chunk_hash(content)
            cache_key = self._make_cache_key(chunk_hash)

            cached_value = await self.redis_client.get(cache_key)

            if cached_value:
                self.logger.debug(f"✅ Cache hit for chunk hash: {chunk_hash[:8]}...")
                return json.loads(cached_value)

            self.logger.debug(f"❌ Cache miss for chunk hash: {chunk_hash[:8]}...")
            return None

        except Exception as e:
            self.logger.error(f"Cache get error: {str(e)}")
            return None

    async def set(self, content: str, result: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Store verification result in cache.

        Args:
            content: Chunk content
            result: Verification result to cache
            ttl: Optional TTL override (uses default if None)

        Returns:
            True if successful, False otherwise
        """
        try:
            chunk_hash = self._compute_chunk_hash(content)
            cache_key = self._make_cache_key(chunk_hash)
            ttl_seconds = ttl if ttl is not None else self.default_ttl

            await self.redis_client.setex(cache_key, ttl_seconds, json.dumps(result))

            self.logger.debug(
                f"✅ Cached result for chunk hash: {chunk_hash[:8]}... " f"(TTL: {ttl_seconds}s)"
            )
            return True

        except Exception as e:
            self.logger.error(f"Cache set error: {str(e)}")
            return False

    async def invalidate(self, content: str) -> bool:
        """
        Invalidate cache entry for specific content.

        Args:
            content: Chunk content to invalidate

        Returns:
            True if successful, False otherwise
        """
        try:
            chunk_hash = self._compute_chunk_hash(content)
            cache_key = self._make_cache_key(chunk_hash)

            deleted = await self.redis_client.delete(cache_key)

            if deleted:
                self.logger.debug(f"✅ Invalidated cache for chunk hash: {chunk_hash[:8]}...")
            return bool(deleted)

        except Exception as e:
            self.logger.error(f"Cache invalidation error: {str(e)}")
            return False

    async def invalidate_pattern(self, pattern: str = "*") -> int:
        """
        Invalidate cache entries matching pattern.

        Args:
            pattern: Redis key pattern (default: all verification cache)

        Returns:
            Number of keys deleted
        """
        try:
            full_pattern = f"{self.CACHE_PREFIX}{pattern}"
            keys = []

            async for key in self.redis_client.scan_iter(match=full_pattern):
                keys.append(key)

            if keys:
                deleted = await self.redis_client.delete(*keys)
                self.logger.info(f"✅ Invalidated {deleted} cache entries")
                return deleted

            return 0

        except Exception as e:
            self.logger.error(f"Pattern invalidation error: {str(e)}")
            return 0

    async def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats (total_keys, memory_usage)
        """
        try:
            # Count keys
            total_keys = 0
            async for _ in self.redis_client.scan_iter(match=f"{self.CACHE_PREFIX}*"):
                total_keys += 1

            # Get memory info
            info = await self.redis_client.info("memory")
            memory_used = info.get("used_memory", 0)

            return {"total_keys": total_keys, "memory_bytes": memory_used}

        except Exception as e:
            self.logger.error(f"Failed to get cache stats: {str(e)}")
            return {"total_keys": 0, "memory_bytes": 0}

    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            self.logger.info("✅ Closed verification cache connection")
