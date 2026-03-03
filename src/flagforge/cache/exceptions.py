"""Custom exceptions for the cache layer."""


class CacheError(Exception):
    """Base exception for all cache-related errors.

    This is the parent exception class for all cache operations.
    Catch this exception to handle any cache-related errors generically.

    Raised when:
        - Cache operation fails due to internal errors
        - Invalid cache configuration
        - Serialization/deserialization errors
    """

    pass


class CacheConnectionError(CacheError):
    """Exception raised when Redis connection fails.

    This exception indicates a connection-level failure to the cache
    backend (typically Redis). The fail-open pattern should catch
    these and degrade gracefully.

    Raised when:
        - Cannot connect to Redis server
        - Connection pool exhausted
        - Connection timeout
        - Authentication failure with Redis
    """

    pass
