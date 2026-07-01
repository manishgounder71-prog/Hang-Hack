"""
Redis-based caching service for Genesis AI.

Provides async cache operations with configurable TTL, connection pooling,
automatic key prefixing, and cache invalidation by pattern.
"""
from __future__ import annotations
import json
import hashlib
import logging
from typing import Any, Optional, Callable

from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as aioredis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    logger.warning("redis not installed — using no-op cache fallback")


def _make_key(prefix: str, *parts: str, **kwargs) -> str:
    """Build a namespaced cache key: {prefix}:{part1}:{part2}:...:{hash(kwargs)}"""
    key_parts = [prefix] + list(parts)
    if kwargs:
        serialized = json.dumps(kwargs, sort_keys=True)
        kw_hash = hashlib.md5(serialized.encode()).hexdigest()[:8]
        key_parts.append(kw_hash)
    return ":".join(key_parts)


class CacheService:
    """Async Redis cache with connection pooling, prefix isolation, and graceful fallback."""

    def __init__(self, redis_url: str | None = None, prefix: str = "genesis"):
        self._redis_url = redis_url or settings.REDIS_URL
        self._prefix = prefix
        self._client: Optional["aioredis.Redis"] = None
        self._enabled = HAS_REDIS

    async def initialize(self) -> bool:
        """Create the Redis connection pool. Returns True if successful."""
        if not self._enabled:
            logger.info("Redis unavailable — cache is a no-op")
            return False
        try:
            self._client = aioredis.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
                retry_on_timeout=True,
                health_check_interval=30,
            )
            await self._client.ping()
            logger.info("Redis cache connected")
            return True
        except Exception as e:
            logger.warning(f"Redis connection failed ({e}) — running without cache")
            self._enabled = False
            self._client = None
            return False

    async def close(self):
        """Close the Redis connection pool."""
        if self._client:
            await self._client.aclose()
            self._client = None
            self._enabled = False

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve a JSON-decoded value from cache. Returns None on miss."""
        if not self._enabled or not self._client:
            return None
        try:
            full_key = f"{self._prefix}:{key}"
            raw = await self._client.get(full_key)
            if raw is not None:
                return json.loads(raw)
            return None
        except Exception as e:
            logger.debug(f"Cache GET error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Store a JSON-encoded value with TTL (seconds). Default 5 min."""
        if not self._enabled or not self._client:
            return False
        try:
            full_key = f"{self._prefix}:{key}"
            raw = json.dumps(value, default=str)
            await self._client.setex(full_key, ttl, raw)
            return True
        except Exception as e:
            logger.debug(f"Cache SET error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Remove a single key from cache."""
        if not self._enabled or not self._client:
            return False
        try:
            full_key = f"{self._prefix}:{key}"
            await self._client.delete(full_key)
            return True
        except Exception as e:
            logger.debug(f"Cache DEL error: {e}")
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """Delete all keys matching a glob pattern, e.g. 'dashboard:*'."""
        if not self._enabled or not self._client:
            return 0
        try:
            full_pattern = f"{self._prefix}:{pattern}"
            cursor = 0
            deleted = 0
            while True:
                cursor, keys = await self._client.scan(cursor, match=full_pattern, count=100)
                if keys:
                    await self._client.delete(*keys)
                    deleted += len(keys)
                if cursor == 0:
                    break
            if deleted:
                logger.debug(f"Cache invalidated {deleted} keys matching '{pattern}'")
            return deleted
        except Exception as e:
            logger.debug(f"Cache INVALIDATE error: {e}")
            return 0

    async def get_or_set(
        self,
        key: str,
        factory: Callable,
        ttl: int = 300,
        force_refresh: bool = False,
    ) -> Any:
        """Cache-aside pattern: return cached value or call factory, cache result."""
        if not force_refresh:
            cached = await self.get(key)
            if cached is not None:
                return cached
        value = await factory()
        await self.set(key, value, ttl)
        return value

    # ── Convenience helpers for entity-specific caching ──

    async def cache_dashboard(self, user_id: str, data: dict, ttl: int = 60) -> bool:
        """Cache dashboard data for a user (short TTL — 1 min)."""
        return await self.set(f"dashboard:{user_id}", data, ttl)

    async def get_dashboard(self, user_id: str) -> Optional[dict]:
        """Get cached dashboard data for a user."""
        return await self.get(f"dashboard:{user_id}")

    async def invalidate_dashboard(self, user_id: str = "*") -> int:
        """Invalidate dashboard cache for one or all users."""
        return await self.invalidate_pattern(f"dashboard:{user_id}")

    async def cache_memories(self, user_id: str, query: str, limit: int, data: list, ttl: int = 120) -> bool:
        """Cache memory list results (2 min TTL)."""
        return await self.set(f"memories:list:{user_id}:q={query}:lim={limit}", data, ttl)

    async def get_memories(self, user_id: str, query: str, limit: int) -> Optional[list]:
        """Get cached memory list."""
        return await self.get(f"memories:list:{user_id}:q={query}:lim={limit}")

    async def invalidate_memories(self, user_id: str = "*") -> int:
        """Invalidate all memory caches for a user."""
        return await self.invalidate_pattern(f"memories:*:{user_id}:*")

    async def cache_memory_stats(self, user_id: str, data: dict, ttl: int = 120) -> bool:
        """Cache memory stats (2 min TTL)."""
        return await self.set(f"memories:stats:{user_id}", data, ttl)

    async def get_memory_stats(self, user_id: str) -> Optional[dict]:
        """Get cached memory stats."""
        return await self.get(f"memories:stats:{user_id}")

    async def is_healthy(self) -> bool:
        """Check if the cache backend is reachable."""
        if not self._enabled or not self._client:
            return False
        try:
            await self._client.ping()
            return True
        except Exception:
            return False


# Module-level singleton
cache = CacheService()
