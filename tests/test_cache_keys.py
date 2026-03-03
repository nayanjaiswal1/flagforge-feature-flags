from flagforge.cache.keys import CacheKeys


def test_cache_keys_constants():
    assert CacheKeys.PREFIX == "ff:"
    assert CacheKeys.RESOLVED_PREFIX == "ff:resolved:"


def test_resolved_key():
    assert CacheKeys.resolved_key("t1", "f1") == "ff:resolved:t1:f1"
    assert CacheKeys.resolved_key(None, "f1") == "ff:resolved:f1"


def test_user_key():
    assert CacheKeys.user_key("t1", "u1", "f1") == "ff:user:t1:u1:f1"
    assert CacheKeys.user_key(None, "u1", "f1") == "ff:user:u1:f1"


def test_definition_key():
    assert CacheKeys.definition_key("f1") == "ff:def:f1"


def test_has_targeting():
    from flagforge.core.models import TenantOverride

    assert CacheKeys.has_targeting(None) is False
    assert CacheKeys.has_targeting(TenantOverride(key="f1", tenant_id="t1")) is False
    assert (
        CacheKeys.has_targeting(TenantOverride(key="f1", tenant_id="t1", enabled_for_users=["u1"]))
        is True
    )
    assert (
        CacheKeys.has_targeting(TenantOverride(key="f1", tenant_id="t1", enabled_for_groups=["g1"]))
        is True
    )


def test_select_key():
    from flagforge.core.models import TenantOverride

    # Resolved key (no override or no targeting)
    key, ttl = CacheKeys.select_key("t1", "u1", "f1", None)
    assert key == "ff:resolved:t1:f1"
    assert ttl == CacheKeys.TTL_RESOLVED

    # User key (targeting)
    override = TenantOverride(key="f1", tenant_id="t1", enabled_for_users=["u1"])
    key, ttl = CacheKeys.select_key("t1", "u1", "f1", override)
    assert key == "ff:user:t1:u1:f1"
    assert ttl == CacheKeys.TTL_USER


def test_select_key_for_context():
    from flagforge.core.models import TenantOverride

    key = CacheKeys.select_key_for_context("t1", "u1", "f1", None)
    assert key == "ff:resolved:t1:f1"

    override = TenantOverride(key="f1", tenant_id="t1", enabled_for_users=["u1"])
    key = CacheKeys.select_key_for_context("t1", "u1", "f1", override)
    assert key == "ff:user:t1:u1:f1"
