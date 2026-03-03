"""Cache backend abstractions."""

from abc import ABC, abstractmethod


class CacheBackend(ABC):
    """Abstract base class for synchronous cache backends.

    Defines the interface for all cache implementations that provide
    flag evaluation caching with optional TTL support.

    Tristate return values for get():
    - None: Cache miss (key not found)
    - False: Cached value indicates flag is DISABLED
    - True: Cached value indicates flag is ENABLED
    """

    @abstractmethod
    def get(self, key: str) -> bool | None:
        """Retrieve a cached flag value by key.

        Args:
            key: The cache key (typically flag_key or flag_key:tenant_id)

        Returns:
            Optional[bool]: True if flag is enabled, False if disabled,
                          None if cache miss
        """
        pass

    @abstractmethod
    def set(self, key: str, value: bool, ttl: int = 60) -> None:
        """Store a flag value in cache with TTL.

        Args:
            key: The cache key
            value: The boolean flag value
            ttl: Time-to-live in seconds (default 60)
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete a specific key from cache.

        Args:
            key: The cache key to delete
        """
        pass

    @abstractmethod
    def delete_for_flag(self, flag_key: str) -> None:
        """Delete all cached values for a specific flag.

        This removes both the base flag cache entry and any
        tenant-specific overrides for this flag.

        Args:
            flag_key: The flag key to invalidate
        """
        pass

    @abstractmethod
    def delete_for_tenant(self, tenant_id: str) -> None:
        """Delete all cached values for a specific tenant.

        This removes all cached flag values that belong to
        the specified tenant.

        Args:
            tenant_id: The tenant identifier
        """
        pass

    @abstractmethod
    def clear_request_cache(self) -> None:
        """Clear all cached values for the current request.

        Use this at the start of a new request to ensure
        fresh flag evaluations.
        """
        pass


class AsyncCacheBackend(ABC):
    """Abstract base class for asynchronous cache backends.

    Defines the interface for async cache implementations that provide
    flag evaluation caching with optional TTL support.

    Tristate return values for get():
    - None: Cache miss (key not found)
    - False: Cached value indicates flag is DISABLED
    - True: Cached value indicates flag is ENABLED
    """

    @abstractmethod
    async def get(self, key: str) -> bool | None:
        """Retrieve a cached flag value by key.

        Args:
            key: The cache key (typically flag_key or flag_key:tenant_id)

        Returns:
            Optional[bool]: True if flag is enabled, False if disabled,
                          None if cache miss
        """
        pass

    @abstractmethod
    async def set(self, key: str, value: bool, ttl: int = 60) -> None:
        """Store a flag value in cache with TTL.

        Args:
            key: The cache key
            value: The boolean flag value
            ttl: Time-to-live in seconds (default 60)
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete a specific key from cache.

        Args:
            key: The cache key to delete
        """
        pass

    @abstractmethod
    async def delete_for_flag(self, flag_key: str) -> None:
        """Delete all cached values for a specific flag.

        This removes both the base flag cache entry and any
        tenant-specific overrides for this flag.

        Args:
            flag_key: The flag key to invalidate
        """
        pass

    @abstractmethod
    async def delete_for_tenant(self, tenant_id: str) -> None:
        """Delete all cached values for a specific tenant.

        This removes all cached flag values that belong to
        the specified tenant.

        Args:
            tenant_id: The tenant identifier
        """
        pass

    @abstractmethod
    async def clear_request_cache(self) -> None:
        """Clear all cached values for the current request.

        Use this at the start of a new request to ensure
        fresh flag evaluations.
        """
        pass
