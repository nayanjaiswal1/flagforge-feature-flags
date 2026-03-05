"""FlagForge Django settings with defaults."""

from django.conf import settings


def _s(name, default):
    return getattr(settings, name, default)


def tenancy_mode() -> str:
    return _s("FLAGFORGE_TENANCY_MODE", "column")


def default_tenant_id() -> str:
    return _s("FLAGFORGE_DEFAULT_TENANT_ID", "default")


def environment() -> str:
    return _s("FLAGFORGE_ENVIRONMENT", "production")


def cache_backend() -> str:
    return _s("FLAGFORGE_CACHE_BACKEND", "local")


def redis_url() -> str | None:
    return _s("FLAGFORGE_REDIS_URL", None)


def redis_host() -> str:
    return _s("FLAGFORGE_REDIS_HOST", "localhost")


def redis_port() -> int:
    return _s("FLAGFORGE_REDIS_PORT", 6379)


def redis_db() -> int:
    return _s("FLAGFORGE_REDIS_DB", 0)


def redis_password() -> str | None:
    return _s("FLAGFORGE_REDIS_PASSWORD", None)


def cache_ttl() -> int:
    return _s("FLAGFORGE_CACHE_TTL", 300)


def tenant_resolver() -> str | None:
    return _s("FLAGFORGE_TENANT_RESOLVER", None)


def user_resolver() -> str | None:
    return _s("FLAGFORGE_USER_RESOLVER", None)


def admin_permission() -> str:
    return _s("FLAGFORGE_ADMIN_PERMISSION", "rest_framework.permissions.IsAdminUser")
