"""Django engine singleton and utilities for FlagForge."""

import importlib

from django.http import HttpRequest

from flagforge.contrib.django import conf
from flagforge.contrib.django.storage import DjangoStorageAdapter
from flagforge.core.context import FeatureContext
from flagforge.core.engine import FlagEngine

_engine = None


def _build_cache():
    """Build the cache backend from FLAGFORGE_CACHE_BACKEND setting.

    Supports:
    - "local"  → LocalCache (default, request-scoped)
    - "none"   → NullCache  (no caching)
    - "redis"  → RedisCache (uses FLAGFORGE_REDIS_* settings)
    - "dotted.path.ClassName" → imports and instantiates that class
    """
    backend = conf.cache_backend()

    if backend == "local":
        from flagforge.cache import LocalCache

        return LocalCache()

    if backend == "none":
        from flagforge.cache import NullCache

        return NullCache()

    if backend == "redis":
        from flagforge.cache import RedisCache

        kwargs = {
            "host": conf.redis_host(),
            "port": conf.redis_port(),
            "db": conf.redis_db(),
            "default_ttl": conf.cache_ttl(),
        }
        password = conf.redis_password()
        if password:
            kwargs["password"] = password
        url = conf.redis_url()
        if url:
            # redis-py accepts a URL directly
            import redis as _redis

            pool = _redis.ConnectionPool.from_url(url, decode_responses=True)
            import redis as _r

            client = _r.Redis(connection_pool=pool)
            cache = RedisCache.__new__(RedisCache)
            cache.key_prefix = "ff:"
            cache.default_ttl = conf.cache_ttl()
            cache._pool = pool
            cache._redis = client
            return cache
        return RedisCache(**kwargs)

    # Dotted path to a custom class — import and instantiate with no args
    module_path, class_name = backend.rsplit(".", 1)
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    return cls()


def _import_callable(dotted_path: str):
    """Import a callable from a dotted path string."""
    module_path, attr = dotted_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, attr)


def get_engine() -> FlagEngine:
    """Get or create a singleton FlagEngine instance for Django."""
    global _engine
    if _engine is None:
        storage = DjangoStorageAdapter()
        cache = _build_cache()
        _engine = FlagEngine(storage=storage, cache=cache)
    return _engine


def _resolve_tenant(request: HttpRequest) -> str | None:
    """Resolve tenant_id from request using FLAGFORGE_TENANT_RESOLVER or built-in logic."""
    resolver_path = conf.tenant_resolver()
    if resolver_path:
        return _import_callable(resolver_path)(request)

    # Built-in: request.tenant_id → request.tenant.schema_name → request.tenant
    tenant_id = getattr(request, "tenant_id", None)
    if not tenant_id and hasattr(request, "tenant"):
        tenant_id = getattr(request.tenant, "schema_name", str(request.tenant))
    return tenant_id or None


def _resolve_user(request: HttpRequest) -> tuple[str | None, list[str]]:
    """Resolve (user_id, group_ids) from request using FLAGFORGE_USER_RESOLVER or built-in logic."""
    resolver_path = conf.user_resolver()
    if resolver_path:
        return _import_callable(resolver_path)(request)

    # Built-in: Django auth
    user_id = None
    group_ids: list[str] = []
    if hasattr(request, "user") and request.user.is_authenticated:
        user_id = str(request.user.id)
        if hasattr(request.user, "groups"):
            group_ids = [str(g.id) for g in request.user.groups.all()]
    return user_id, group_ids


def flag_enabled(key: str, request: HttpRequest | None = None) -> bool:
    """Check if a feature flag is enabled.

    Args:
        key: Feature flag key
        request: Optional Django request for automatic context extraction

    Returns:
        bool: Whether the flag is enabled
    """
    engine = get_engine()

    tenant_id: str | None = None
    user_id: str | None = None
    group_ids: list[str] = []
    environment = conf.environment()

    if request:
        tenant_id = _resolve_tenant(request)
        user_id, group_ids = _resolve_user(request)

    if not tenant_id:
        tenant_id = conf.default_tenant_id()

    context = FeatureContext(
        tenant_id=tenant_id,
        user_id=user_id,
        group_ids=group_ids,
        environment=environment,
    )

    return engine.is_enabled(key, context)
