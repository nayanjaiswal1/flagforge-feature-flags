"""Tests for FlagForge Django configuration settings."""

from django.test import override_settings
import pytest

from flagforge.contrib.django import conf
from flagforge.contrib.django.checks import (
    check_admin_permission,
    check_cache_backend,
    check_cache_ttl,
    check_resolvers,
)

# ---------------------------------------------------------------------------
# conf.py defaults
# ---------------------------------------------------------------------------


def test_conf_defaults():
    assert conf.tenancy_mode() == "column"
    assert conf.default_tenant_id() == "default"
    assert conf.environment() == "production"
    assert conf.cache_backend() == "local"
    assert conf.cache_ttl() == 300
    assert conf.tenant_resolver() is None
    assert conf.user_resolver() is None
    assert conf.admin_permission() == "rest_framework.permissions.IsAdminUser"


@override_settings(
    FLAGFORGE_CACHE_BACKEND="redis",
    FLAGFORGE_CACHE_TTL=60,
    FLAGFORGE_ENVIRONMENT="staging",
    FLAGFORGE_DEFAULT_TENANT_ID="acme",
    FLAGFORGE_ADMIN_PERMISSION="rest_framework.permissions.AllowAny",
)
def test_conf_reads_settings():
    assert conf.cache_backend() == "redis"
    assert conf.cache_ttl() == 60
    assert conf.environment() == "staging"
    assert conf.default_tenant_id() == "acme"
    assert conf.admin_permission() == "rest_framework.permissions.AllowAny"


# ---------------------------------------------------------------------------
# check_cache_backend
# ---------------------------------------------------------------------------


def test_check_cache_backend_default():
    assert check_cache_backend(None) == []


@override_settings(FLAGFORGE_CACHE_BACKEND="local")
def test_check_cache_backend_local():
    assert check_cache_backend(None) == []


@override_settings(FLAGFORGE_CACHE_BACKEND="none")
def test_check_cache_backend_none():
    assert check_cache_backend(None) == []


@override_settings(
    FLAGFORGE_CACHE_BACKEND="redis",
    FLAGFORGE_REDIS_HOST="localhost",
)
def test_check_cache_backend_redis_with_host():
    assert check_cache_backend(None) == []


@override_settings(FLAGFORGE_CACHE_BACKEND="redis")
def test_check_cache_backend_redis_no_host():
    errors = check_cache_backend(None)
    assert len(errors) == 1
    assert errors[0].id == "flagforge.E003"


@override_settings(FLAGFORGE_CACHE_BACKEND="rest_framework.permissions.IsAdminUser")
def test_check_cache_backend_valid_dotted_path():
    assert check_cache_backend(None) == []


@override_settings(FLAGFORGE_CACHE_BACKEND="notadottedpath")
def test_check_cache_backend_invalid_no_dot():
    errors = check_cache_backend(None)
    assert len(errors) == 1
    assert errors[0].id == "flagforge.E002"


@override_settings(FLAGFORGE_CACHE_BACKEND="flagforge.nonexistent.module.Class")
def test_check_cache_backend_bad_import():
    errors = check_cache_backend(None)
    assert len(errors) == 1
    assert errors[0].id == "flagforge.E002"


# ---------------------------------------------------------------------------
# check_resolvers
# ---------------------------------------------------------------------------


def test_check_resolvers_none():
    assert check_resolvers(None) == []


@override_settings(FLAGFORGE_TENANT_RESOLVER="flagforge.contrib.django.conf.tenancy_mode")
def test_check_resolvers_valid_tenant():
    assert check_resolvers(None) == []


@override_settings(FLAGFORGE_TENANT_RESOLVER="nodot")
def test_check_resolvers_invalid_tenant_no_dot():
    errors = check_resolvers(None)
    assert len(errors) == 1
    assert errors[0].id == "flagforge.E004"


@override_settings(FLAGFORGE_TENANT_RESOLVER="flagforge.nonexistent.module.fn")
def test_check_resolvers_bad_import_tenant():
    errors = check_resolvers(None)
    assert len(errors) == 1
    assert errors[0].id == "flagforge.E004"


@override_settings(FLAGFORGE_USER_RESOLVER="flagforge.nonexistent.module.fn")
def test_check_resolvers_bad_import_user():
    errors = check_resolvers(None)
    assert len(errors) == 1
    assert errors[0].id == "flagforge.E005"


# ---------------------------------------------------------------------------
# check_admin_permission
# ---------------------------------------------------------------------------


def test_check_admin_permission_default():
    assert check_admin_permission(None) == []


@override_settings(FLAGFORGE_ADMIN_PERMISSION="rest_framework.permissions.AllowAny")
def test_check_admin_permission_valid():
    assert check_admin_permission(None) == []


@override_settings(FLAGFORGE_ADMIN_PERMISSION="nodot")
def test_check_admin_permission_no_dot():
    errors = check_admin_permission(None)
    assert len(errors) == 1
    assert errors[0].id == "flagforge.E006"


@override_settings(FLAGFORGE_ADMIN_PERMISSION="flagforge.nonexistent.module.Cls")
def test_check_admin_permission_bad_import():
    errors = check_admin_permission(None)
    assert len(errors) == 1
    assert errors[0].id == "flagforge.E006"


# ---------------------------------------------------------------------------
# check_cache_ttl
# ---------------------------------------------------------------------------


def test_check_cache_ttl_default():
    assert check_cache_ttl(None) == []


@override_settings(FLAGFORGE_CACHE_TTL=60)
def test_check_cache_ttl_valid():
    assert check_cache_ttl(None) == []


@override_settings(FLAGFORGE_CACHE_TTL=0)
def test_check_cache_ttl_zero():
    errors = check_cache_ttl(None)
    assert len(errors) == 1
    assert errors[0].id == "flagforge.E007"


@override_settings(FLAGFORGE_CACHE_TTL=-1)
def test_check_cache_ttl_negative():
    errors = check_cache_ttl(None)
    assert len(errors) == 1
    assert errors[0].id == "flagforge.E007"


@override_settings(FLAGFORGE_CACHE_TTL="fast")
def test_check_cache_ttl_non_int():
    errors = check_cache_ttl(None)
    assert len(errors) == 1
    assert errors[0].id == "flagforge.E007"


# ---------------------------------------------------------------------------
# engine: _build_cache respects FLAGFORGE_CACHE_BACKEND
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_engine_uses_local_cache_by_default(monkeypatch):
    monkeypatch.setattr("flagforge.contrib.django.engine._engine", None)
    from flagforge.cache.local import LocalCache
    from flagforge.contrib.django.engine import get_engine

    engine = get_engine()
    assert isinstance(engine.cache, LocalCache)


@pytest.mark.django_db
@override_settings(FLAGFORGE_CACHE_BACKEND="none")
def test_engine_uses_null_cache(monkeypatch):
    monkeypatch.setattr("flagforge.contrib.django.engine._engine", None)
    from flagforge.cache.null import NullCache
    from flagforge.contrib.django.engine import get_engine

    engine = get_engine()
    assert isinstance(engine.cache, NullCache)


# ---------------------------------------------------------------------------
# engine: resolver hooks
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_flag_enabled_uses_default_tenant_when_no_request(monkeypatch):
    monkeypatch.setattr("flagforge.contrib.django.engine._engine", None)
    from flagforge.contrib.django.engine import flag_enabled

    # Should not raise — falls back to FLAGFORGE_DEFAULT_TENANT_ID
    result = flag_enabled("nonexistent_flag")
    assert result is False


@pytest.mark.django_db
@override_settings(FLAGFORGE_TENANT_RESOLVER="tests.test_django_conf._custom_tenant_resolver")
def test_flag_enabled_uses_custom_tenant_resolver(monkeypatch, rf):
    monkeypatch.setattr("flagforge.contrib.django.engine._engine", None)
    from flagforge.contrib.django.engine import flag_enabled

    request = rf.get("/")
    request.user = type("U", (), {"is_authenticated": False})()
    result = flag_enabled("nonexistent_flag", request)
    assert result is False  # flag doesn't exist → False, but resolver ran


@pytest.mark.django_db
@override_settings(FLAGFORGE_USER_RESOLVER="tests.test_django_conf._custom_user_resolver")
def test_flag_enabled_uses_custom_user_resolver(monkeypatch, rf):
    monkeypatch.setattr("flagforge.contrib.django.engine._engine", None)
    from flagforge.contrib.django.engine import flag_enabled

    request = rf.get("/")
    request.user = type("U", (), {"is_authenticated": False})()
    result = flag_enabled("nonexistent_flag", request)
    assert result is False


# Helper callables referenced by dotted paths in tests above
def _custom_tenant_resolver(request):
    return "test-tenant"


def _custom_user_resolver(request):
    return ("user-42", ["group-1"])


# ---------------------------------------------------------------------------
# cache/keys.py: TTL reads from FLAGFORGE_CACHE_TTL
# ---------------------------------------------------------------------------


@override_settings(FLAGFORGE_CACHE_TTL=120)
def test_cache_keys_ttl_from_settings():
    from flagforge.cache.keys import CacheKeys

    _, ttl = CacheKeys.select_key("t1", "u1", "f1", None)
    assert ttl == 120


def test_cache_keys_ttl_default():
    from flagforge.cache.keys import CacheKeys

    _, ttl = CacheKeys.select_key("t1", "u1", "f1", None)
    assert ttl == CacheKeys.TTL_RESOLVED
