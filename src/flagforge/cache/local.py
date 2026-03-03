"""Local in-memory cache using contextvars for request-scoped isolation."""


from flagforge.cache.base import AsyncCacheBackend, CacheBackend
from flagforge.core.context import _cache_var


class LocalCache(CacheBackend):
    """Local in-memory cache using contextvars for request-scoped isolation.

    This cache backend stores flag values in the request-local context,
    providing automatic isolation between requests. Each request gets
    its own fresh cache that is cleared when the request context ends.

    The cache uses a simple dict internally, stored in the contextvar
    provided by flagforge.core.context.

    Key format:
    - Base flag: 'flag:<flag_key>'
    - Tenant override: 'tenant:<tenant_id>:<flag_key>'
    """

    def get(self, key: str) -> bool | None:
        """Retrieve a cached flag value by key.

        Args:
            key: The cache key

        Returns:
            Optional[bool]: The cached value, or None if not found
        """
        cache = _cache_var.get()
        if cache is None:
            return None
        return cache.get(key)

    def set(self, key: str, value: bool, ttl: int = 60) -> None:
        """Store a flag value in the request-local cache.

        Note: TTL is accepted for interface compatibility but not
        enforced in this in-memory implementation. The cache is
        naturally cleared at request end.

        Args:
            key: The cache key
            value: The boolean flag value
            ttl: Time-to-live in seconds (default 60, not enforced)
        """
        cache = _cache_var.get()
        if cache is not None:
            cache[key] = value

    def delete(self, key: str) -> None:
        """Delete a specific key from cache.

        Args:
            key: The cache key to delete
        """
        cache = _cache_var.get()
        if cache is not None:
            cache.pop(key, None)

    def delete_for_flag(self, flag_key: str) -> None:
        """Delete all cached values for a specific flag.

        Removes all cache entries matching this flag key across all tenants.

        Args:
            flag_key: The flag key to invalidate
        """
        cache = _cache_var.get()
        if cache is None:
            return

        prefix = f"{flag_key}:"
        keys_to_remove = [key for key in cache if key == flag_key or key.startswith(prefix)]

        for key in keys_to_remove:
            del cache[key]

    def delete_for_tenant(self, tenant_id: str) -> None:
        """Delete all cached values for a specific tenant.

        Args:
            tenant_id: The tenant identifier
        """
        cache = _cache_var.get()
        if cache is None:
            return

        prefix = f":{tenant_id}:"
        suffix = f":{tenant_id}"
        keys_to_remove = [key for key in cache if prefix in key or key.endswith(suffix)]

        for key in keys_to_remove:
            del cache[key]

    def clear_request_cache(self) -> None:
        """Clear all cached values for the current request."""
        cache = _cache_var.get()
        if cache is not None:
            cache.clear()


class AsyncLocalCache(AsyncCacheBackend):
    """Async local in-memory cache using contextvars for request-scoped isolation.

    This async cache backend provides the same functionality as LocalCache
    but with async-compatible method signatures.
    """

    async def get(self, key: str) -> bool | None:
        """Retrieve a cached flag value by key.

        Args:
            key: The cache key

        Returns:
            Optional[bool]: The cached value, or None if not found
        """
        cache = _cache_var.get()
        if cache is None:
            return None
        return cache.get(key)

    async def set(self, key: str, value: bool, ttl: int = 60) -> None:
        """Store a flag value in the request-local cache.

        Note: TTL is accepted for interface compatibility but not
        enforced in this in-memory implementation.

        Args:
            key: The cache key
            value: The boolean flag value
            ttl: Time-to-live in seconds (default 60, not enforced)
        """
        cache = _cache_var.get()
        if cache is not None:
            cache[key] = value

    async def delete(self, key: str) -> None:
        """Delete a specific key from cache.

        Args:
            key: The cache key to delete
        """
        cache = _cache_var.get()
        if cache is not None:
            cache.pop(key, None)

    async def delete_for_flag(self, flag_key: str) -> None:
        """Delete all cached values for a specific flag.

        Args:
            flag_key: The flag key to invalidate
        """
        cache = _cache_var.get()
        if cache is None:
            return

        prefix = f"{flag_key}:"
        keys_to_remove = [key for key in cache if key == flag_key or key.startswith(prefix)]

        for key in keys_to_remove:
            del cache[key]

    async def delete_for_tenant(self, tenant_id: str) -> None:
        """Delete all cached values for a specific tenant.

        Args:
            tenant_id: The tenant identifier
        """
        cache = _cache_var.get()
        if cache is None:
            return

        prefix = f":{tenant_id}:"
        suffix = f":{tenant_id}"
        keys_to_remove = [key for key in cache if prefix in key or key.endswith(suffix)]

        for key in keys_to_remove:
            del cache[key]

    async def clear_request_cache(self) -> None:
        """Clear all cached values for the current request."""
        cache = _cache_var.get()
        if cache is not None:
            cache.clear()
