# FlagForge - Enterprise Multi-Tenant Feature Flag Control Plane
"""FlagForge public API."""

# Core engines
# Cache backends (cache exceptions are also exported via cache module)
from flagforge.cache import (
    AsyncCacheBackend,
    AsyncLocalCache,
    AsyncNullCache,
    CacheBackend,
    CacheConnectionError,
    CacheError,
    LocalCache,
    NullCache,
)

# Context and request management
from flagforge.core.context import (
    TENANT_MODE_COLUMN,
    TENANT_MODE_SCHEMA,
    FeatureContext,
    async_request_context,
    request_context,
)
from flagforge.core.engine import AsyncFlagEngine, FlagEngine

# Exceptions
from flagforge.core.exceptions import FlagForgeError, StorageError

# Redis cache backends are lazy-loaded — only available when `redis` is installed.
# Access via: from flagforge.cache import RedisCache, AsyncRedisCache


def is_enabled(key: str, context: FeatureContext) -> bool:
    """Check if a feature flag is enabled for the given context.

    This is a convenience function that uses a global default engine.
    You must configure the engine first using configure_engine().

    Args:
        key: Feature flag key
        context: Evaluation context

    Returns:
        bool: Whether the flag is enabled

    Raises:
        ValueError: If key is empty or context.tenant_id is None
        RuntimeError: If no engine has been configured
    """
    from inspect import iscoroutinefunction

    if not key:
        raise ValueError("Feature flag key cannot be empty")

    engine = get_engine()
    if engine is None:
        raise RuntimeError("Configure the engine first using flagforge.configure_engine(engine)")

    if iscoroutinefunction(engine.is_enabled):
        raise RuntimeError(
            "Use 'async is_enabled()' with AsyncFlagEngine. "
            "Use await flagforge.is_enabled() with async engine."
        )

    return engine.is_enabled(key, context)  # type: ignore[return-value]


def evaluate_many(keys: list[str], context: FeatureContext) -> dict[str, bool]:
    """Evaluate multiple feature flags in a single round-trip.

    This is a convenience function that uses a global default engine.
    You must configure the engine first using configure_engine().

    Args:
        keys: List of feature flag keys to evaluate
        context: Evaluation context

    Returns:
        dict[str, bool]: Mapping of flag keys to enabled state

    Raises:
        ValueError: If keys is empty or context.tenant_id is None
        RuntimeError: If no engine has been configured
    """
    from inspect import iscoroutinefunction

    if not keys:
        raise ValueError("Feature flag keys list cannot be empty")

    engine = get_engine()
    if engine is None:
        raise RuntimeError("Configure the engine first using flagforge.configure_engine(engine)")

    if iscoroutinefunction(engine.evaluate_many):
        raise RuntimeError("Use 'async evaluate_many()' with AsyncFlagEngine. ")

    return engine.evaluate_many(keys, context)  # type: ignore[return-value]


# Convenience function to set global engine (to be implemented in later phase)
_global_engine: FlagEngine | AsyncFlagEngine | None = None


def configure_engine(engine: FlagEngine | AsyncFlagEngine) -> None:
    """Configure the global FlagEngine instance.

    Args:
        engine: A FlagEngine or AsyncFlagEngine instance
    """
    global _global_engine
    _global_engine = engine


def get_engine() -> FlagEngine | AsyncFlagEngine | None:
    """Get the configured global engine.

    Returns:
        The configured engine or None if not configured
    """
    return _global_engine


__all__ = [
    # Tenant modes
    "TENANT_MODE_COLUMN",
    "TENANT_MODE_SCHEMA",
    "AsyncCacheBackend",
    "AsyncFlagEngine",
    "AsyncLocalCache",
    "AsyncNullCache",
    # Cache backends
    "CacheBackend",
    "CacheConnectionError",
    "CacheError",
    # Context
    "FeatureContext",
    # Engines
    "FlagEngine",
    # Exceptions
    "FlagForgeError",
    "LocalCache",
    "NullCache",
    "StorageError",
    "async_request_context",
    "configure_engine",
    "evaluate_many",
    "get_engine",
    # RedisCache / AsyncRedisCache: lazy, from flagforge.cache import RedisCache
    # Convenience functions
    "is_enabled",
    "request_context",
]
