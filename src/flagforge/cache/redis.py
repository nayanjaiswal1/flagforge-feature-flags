"""Redis cache implementations using redis-py and redis.asyncio."""

import logging
from typing import cast

import redis
import redis.asyncio

from flagforge.cache.base import AsyncCacheBackend, CacheBackend

logger = logging.getLogger(__name__)


class RedisCache(CacheBackend):
    """Synchronous Redis cache implementation.

    Provides distributed caching using Redis with fail-open pattern.
    On connection errors, operations fail gracefully without raising exceptions.

    Cache key format: "{key_prefix}{tenant_id}:{flag_key}[:{user_id}][:environment]"

    Attributes:
        host: Redis server hostname
        port: Redis server port
        db: Redis database number
        key_prefix: Prefix for all cache keys (default: 'ff:')
        default_ttl: Default TTL in seconds for cache entries (default: 60)
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str | None = None,
        key_prefix: str = "ff:",
        default_ttl: int = 60,
    ):
        """Initialize Redis cache client.

        Args:
            host: Redis server hostname
            port: Redis server port
            db: Redis database number
            password: Optional Redis password
            key_prefix: Prefix for all cache keys
            default_ttl: Default TTL in seconds
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.key_prefix = key_prefix
        self.default_ttl = default_ttl

        # Create connection pool and Redis client
        self._pool = redis.ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True,
        )
        self._redis = redis.Redis(connection_pool=self._pool)

    def get(self, key: str) -> bool | None:
        """Retrieve a cached flag value by key.

        Args:
            key: The cache key

        Returns:
            Optional[bool]: True if flag is enabled, False if disabled,
                          None if cache miss or on error
        """
        try:
            full_key = f"{self.key_prefix}{key}"
            value = self._redis.get(full_key)
            if value is None:
                return None
            return str(value).lower() in ("true", "1", "yes")
        except redis.RedisError as e:
            logger.warning(f"Redis get failed for key '{key}': {e}")
            return None

    def set(self, key: str, value: bool, ttl: int | None = None) -> None:
        """Store a flag value in cache with TTL.

        Args:
            key: The cache key
            value: The boolean flag value
            ttl: Time-to-live in seconds (uses default if not specified)
        """
        try:
            full_key = f"{self.key_prefix}{key}"
            ttl = ttl if ttl is not None else self.default_ttl
            # Store as string for proper boolean conversion on retrieval
            self._redis.set(full_key, str(value), ex=ttl)
        except redis.RedisError as e:
            logger.warning(f"Redis set failed for key '{key}': {e}")

    def delete(self, key: str) -> None:
        """Delete a specific key from cache.

        Args:
            key: The cache key to delete
        """
        try:
            full_key = f"{self.key_prefix}{key}"
            self._redis.delete(full_key)
        except redis.RedisError as e:
            logger.warning(f"Redis delete failed for key '{key}': {e}")

    def _find_keys_matching(self, predicate) -> list:
        """Find all keys matching a predicate by scanning and filtering.

        Args:
            predicate: A function that takes a key and returns True if it matches

        Returns:
            List of matching keys
        """
        keys = []
        cursor = 0
        while True:
            cursor, batch = cast(
                tuple[int, list[str]],
                self._redis.scan(cursor, match=f"{self.key_prefix}*", count=100),
            )
            keys.extend([key for key in batch if predicate(key)])
            if cursor == 0:
                break
        return keys

    def delete_for_flag(self, flag_key: str) -> None:
        """Delete all cached values for a specific flag.

        Uses SCAN to find keys matching the flag_key pattern.

        Args:
            flag_key: The flag key to invalidate
        """
        try:
            prefix = self.key_prefix
            flag_prefix = f"{prefix}{flag_key}:"
            keys_to_delete: list[str] = []
            cursor = 0
            while True:
                cursor, batch = cast(
                    tuple[int, list[str]], self._redis.scan(cursor, match=f"{prefix}*", count=100)
                )
                keys_to_delete.extend(
                    key_str for key_str in batch if key_str.startswith(flag_prefix)
                )
                if cursor == 0:
                    break
            if keys_to_delete:
                self._redis.delete(*keys_to_delete)
        except redis.RedisError as e:
            logger.warning(f"Redis delete_for_flag failed for '{flag_key}': {e}")

    def delete_for_tenant(self, tenant_id: str) -> None:
        """Delete all cached values for a specific tenant.

        Uses SCAN to find keys matching the tenant_id pattern.

        Args:
            tenant_id: The tenant identifier
        """
        try:
            prefix = self.key_prefix
            tenant_infix = f":{tenant_id}:"
            keys_to_delete: list[str] = []
            cursor = 0
            while True:
                cursor, batch = cast(
                    tuple[int, list[str]], self._redis.scan(cursor, match=f"{prefix}*", count=100)
                )
                keys_to_delete.extend(key_str for key_str in batch if tenant_infix in key_str)
                if cursor == 0:
                    break
            if keys_to_delete:
                self._redis.delete(*keys_to_delete)
        except redis.RedisError as e:
            logger.warning(f"Redis delete_for_tenant failed for '{tenant_id}': {e}")

    def clear_request_cache(self) -> None:
        """Clear all cached values for the current request.

        No-op for Redis since it's not request-scoped.
        Use delete_for_tenant() or delete_for_flag() for explicit invalidation.
        """
        # Redis is a distributed cache, not request-scoped
        pass


class AsyncRedisCache(AsyncCacheBackend):
    """Asynchronous Redis cache implementation using redis.asyncio.

    Provides distributed async caching using Redis with fail-open pattern.
    On connection errors, operations fail gracefully without raising exceptions.

    Cache key format: "{key_prefix}{tenant_id}:{flag_key}[:{user_id}][:environment]"

    Attributes:
        host: Redis server hostname
        port: Redis server port
        db: Redis database number
        key_prefix: Prefix for all cache keys (default: 'ff:')
        default_ttl: Default TTL in seconds for cache entries (default: 60)
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str | None = None,
        key_prefix: str = "ff:",
        default_ttl: int = 60,
    ):
        """Initialize async Redis cache client.

        Args:
            host: Redis server hostname
            port: Redis server port
            db: Redis database number
            password: Optional Redis password
            key_prefix: Prefix for all cache keys
            default_ttl: Default TTL in seconds
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.key_prefix = key_prefix
        self.default_ttl = default_ttl

        # Create async connection pool and Redis client
        self._pool = redis.asyncio.ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True,
        )
        self._redis = redis.asyncio.Redis(connection_pool=self._pool)

    async def get(self, key: str) -> bool | None:
        """Retrieve a cached flag value by key.

        Args:
            key: The cache key

        Returns:
            Optional[bool]: True if flag is enabled, False if disabled,
                          None if cache miss or on error
        """
        try:
            full_key = f"{self.key_prefix}{key}"
            value = await self._redis.get(full_key)
            if value is None:
                return None
            return str(value).lower() in ("true", "1", "yes")
        except redis.asyncio.RedisError as e:
            logger.warning(f"AsyncRedis get failed for key '{key}': {e}")
            return None

    async def set(self, key: str, value: bool, ttl: int | None = None) -> None:
        """Store a flag value in cache with TTL.

        Args:
            key: The cache key
            value: The boolean flag value
            ttl: Time-to-live in seconds (uses default if not specified)
        """
        try:
            full_key = f"{self.key_prefix}{key}"
            ttl = ttl if ttl is not None else self.default_ttl
            # Store as string for proper boolean conversion on retrieval
            await self._redis.set(full_key, str(value), ex=ttl)
        except redis.asyncio.RedisError as e:
            logger.warning(f"AsyncRedis set failed for key '{key}': {e}")

    async def delete(self, key: str) -> None:
        """Delete a specific key from cache.

        Args:
            key: The cache key to delete
        """
        try:
            full_key = f"{self.key_prefix}{key}"
            await self._redis.delete(full_key)
        except redis.asyncio.RedisError as e:
            logger.warning(f"AsyncRedis delete failed for key '{key}': {e}")

    async def _find_keys_matching(self, predicate) -> list:
        """Find all keys matching a predicate by scanning and filtering.

        Args:
            predicate: A function that takes a key and returns True if it matches

        Returns:
            List of matching keys
        """
        keys = []
        cursor = 0
        while True:
            cursor, batch = cast(
                tuple[int, list[str]],
                await self._redis.scan(cursor, match=f"{self.key_prefix}*", count=100),
            )
            keys.extend([key for key in batch if predicate(key)])
            if cursor == 0:
                break
        return keys

    async def delete_for_flag(self, flag_key: str) -> None:
        """Delete all cached values for a specific flag.

        Uses SCAN to find keys matching the flag_key pattern.

        Args:
            flag_key: The flag key to invalidate
        """
        try:
            prefix = self.key_prefix
            flag_prefix = f"{prefix}{flag_key}:"
            keys_to_delete: list[str] = []
            cursor = 0
            while True:
                cursor, batch = cast(
                    tuple[int, list[str]],
                    await self._redis.scan(cursor, match=f"{prefix}*", count=100),
                )
                keys_to_delete.extend(
                    key_str for key_str in batch if key_str.startswith(flag_prefix)
                )
                if cursor == 0:
                    break
            if keys_to_delete:
                await self._redis.delete(*keys_to_delete)
        except redis.asyncio.RedisError as e:
            logger.warning(f"AsyncRedis delete_for_flag failed for '{flag_key}': {e}")

    async def delete_for_tenant(self, tenant_id: str) -> None:
        """Delete all cached values for a specific tenant.

        Uses SCAN to find keys matching the tenant_id pattern.

        Args:
            tenant_id: The tenant identifier
        """
        try:
            prefix = self.key_prefix
            tenant_infix = f":{tenant_id}:"
            keys_to_delete: list[str] = []
            cursor = 0
            while True:
                cursor, batch = cast(
                    tuple[int, list[str]],
                    await self._redis.scan(cursor, match=f"{prefix}*", count=100),
                )
                keys_to_delete.extend(key_str for key_str in batch if tenant_infix in key_str)
                if cursor == 0:
                    break
            if keys_to_delete:
                await self._redis.delete(*keys_to_delete)
        except redis.asyncio.RedisError as e:
            logger.warning(f"AsyncRedis delete_for_tenant failed for '{tenant_id}': {e}")

    async def clear_request_cache(self) -> None:
        """Clear all cached values for the current request.

        No-op for Redis since it's not request-scoped.
        Use delete_for_tenant() or delete_for_flag() for explicit invalidation.
        """
        # Redis is a distributed cache, not request-scoped
        pass
