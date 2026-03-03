"""Feature context for flag evaluation."""

from contextlib import asynccontextmanager, contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

# Request-local cache using contextvars
_cache_var: ContextVar[dict | None] = ContextVar("flagforge_cache", default=None)


# Multi-tenancy mode constants (TENANT-01, TENANT-02, TENANT-03, TENANT-04)
TENANT_MODE_COLUMN = "column"
TENANT_MODE_SCHEMA = "schema"


@contextmanager
def request_context():
    """Sync context manager for request-local cache initialization.

    Use this for synchronous frameworks like Django or Flask.

    Yields:
        dict: Request-local cache dictionary

    Example:
        with request_context() as cache:
            cache['key'] = 'value'
    """
    cache: dict = {}
    token = _cache_var.set(cache)
    try:
        yield cache
    finally:
        _cache_var.reset(token)
        # Explicitly clear the cache reference
        cache.clear()


@asynccontextmanager
async def async_request_context():
    """Async context manager for request-local cache initialization.

    Use this for async frameworks like FastAPI with BackgroundTasks.

    Yields:
        dict: Request-local cache dictionary

    Example:
        async with async_request_context() as cache:
            cache['key'] = 'value'
    """
    cache: dict = {}
    token = _cache_var.set(cache)
    try:
        yield cache
    finally:
        _cache_var.reset(token)
        # Explicitly clear the cache reference
        cache.clear()


def get_request_cache() -> dict | None:
    """Get the current request-local cache if it exists.

    Returns:
        dict or None: The current request cache or None if not in a context
    """
    return _cache_var.get()


@dataclass
class FeatureContext:
    """Context for feature flag evaluation.

    Attributes:
        tenant_id: Tenant identifier (required for multi-tenancy)
        user_id: User identifier for targeting
        group_ids: List of group IDs the user belongs to
        environment: Environment name (e.g., 'dev', 'staging', 'prod')
        attributes: Custom attributes for advanced targeting
    """

    tenant_id: str | None = None
    user_id: str | None = None
    group_ids: list[str] = field(default_factory=list)
    environment: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
