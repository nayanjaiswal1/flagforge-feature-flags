"""Null cache implementations - no-op caching for development/testing."""

from flagforge.cache.base import AsyncCacheBackend, CacheBackend


class NullCache(CacheBackend):
    """Null cache implementation - all operations are no-ops.

    This cache backend is useful for:
    - Development environments where caching isn't needed
    - Testing scenarios where you want to ensure fresh evaluations
    - Debugging flag behavior without cache interference

    All get() calls return None (cache miss), and set()/delete()
    operations do nothing.
    """

    def get(self, key: str) -> None:
        """Always returns None (cache miss).

        Args:
            key: The cache key (ignored)

        Returns:
            None: Always returns None to indicate cache miss
        """
        return None

    def set(self, key: str, value: bool, ttl: int = 60) -> None:
        """No-op - does nothing.

        Args:
            key: The cache key (ignored)
            value: The boolean flag value (ignored)
            ttl: Time-to-live in seconds (ignored)
        """
        pass

    def delete(self, key: str) -> None:
        """No-op - does nothing.

        Args:
            key: The cache key (ignored)
        """
        pass

    def delete_for_flag(self, flag_key: str) -> None:
        """No-op - does nothing.

        Args:
            flag_key: The flag key (ignored)
        """
        pass

    def delete_for_tenant(self, tenant_id: str) -> None:
        """No-op - does nothing.

        Args:
            tenant_id: The tenant identifier (ignored)
        """
        pass

    def clear_request_cache(self) -> None:
        """No-op - does nothing."""
        pass


class AsyncNullCache(AsyncCacheBackend):
    """Async null cache implementation - all operations are no-ops.

    This async cache backend is useful for:
    - Development environments where caching isn't needed
    - Testing scenarios where you want to ensure fresh evaluations
    - Debugging flag behavior without cache interference

    All get() calls return None (cache miss), and set()/delete()
    operations do nothing.
    """

    async def get(self, key: str) -> None:
        """Always returns None (cache miss).

        Args:
            key: The cache key (ignored)

        Returns:
            None: Always returns None to indicate cache miss
        """
        return None

    async def set(self, key: str, value: bool, ttl: int = 60) -> None:
        """No-op - does nothing.

        Args:
            key: The cache key (ignored)
            value: The boolean flag value (ignored)
            ttl: Time-to-live in seconds (ignored)
        """
        pass

    async def delete(self, key: str) -> None:
        """No-op - does nothing.

        Args:
            key: The cache key (ignored)
        """
        pass

    async def delete_for_flag(self, flag_key: str) -> None:
        """No-op - does nothing.

        Args:
            flag_key: The flag key (ignored)
        """
        pass

    async def delete_for_tenant(self, tenant_id: str) -> None:
        """No-op - does nothing.

        Args:
            tenant_id: The tenant identifier (ignored)
        """
        pass

    async def clear_request_cache(self) -> None:
        """No-op - does nothing."""
        pass
