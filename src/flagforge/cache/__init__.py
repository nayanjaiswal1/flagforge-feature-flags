"""Cache backend implementations for FlagForge.

This module provides cache abstractions and implementations for flag evaluation caching:

- CacheBackend: Abstract base class for synchronous cache backends
- AsyncCacheBackend: Abstract base class for asynchronous cache backends
- NullCache: No-op cache implementation (no caching)
- AsyncNullCache: Async no-op cache implementation
- LocalCache: In-memory cache using contextvars for request-scoped isolation
- AsyncLocalCache: Async in-memory cache using contextvars
- RedisCache: Distributed Redis cache with fail-open pattern
- AsyncRedisCache: Async distributed Redis cache with fail-open pattern
- CacheError: Base exception for cache operations
- CacheConnectionError: Exception for Redis connection failures
"""

from flagforge.cache.base import AsyncCacheBackend, CacheBackend
from flagforge.cache.exceptions import CacheConnectionError, CacheError


def __getattr__(name: str):
    """Lazy-import classes to avoid circular dependencies and optional dependencies."""
    if name in ("RedisCache", "AsyncRedisCache"):
        from flagforge.cache.redis import AsyncRedisCache, RedisCache
        return {"RedisCache": RedisCache, "AsyncRedisCache": AsyncRedisCache}[name]

    if name in ("LocalCache", "AsyncLocalCache"):
        from flagforge.cache.local import AsyncLocalCache, LocalCache
        return {"LocalCache": LocalCache, "AsyncLocalCache": AsyncLocalCache}[name]

    if name in ("NullCache", "AsyncNullCache"):
        from flagforge.cache.null import AsyncNullCache, NullCache
        return {"NullCache": NullCache, "AsyncNullCache": AsyncNullCache}[name]

    raise AttributeError(f"module 'flagforge.cache' has no attribute {name!r}")


__all__ = [
    "AsyncCacheBackend",
    "AsyncLocalCache",
    "AsyncNullCache",
    "AsyncRedisCache",
    # Abstract base classes
    "CacheBackend",
    "CacheConnectionError",
    # Exceptions
    "CacheError",
    # Local cache implementations
    "LocalCache",
    # Null cache implementations
    "NullCache",
    # Redis cache implementations (lazy — requires `pip install flagforge[redis]`)
    "RedisCache",
]
