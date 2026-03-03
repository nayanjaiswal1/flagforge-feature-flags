"""Tests for the core FlagEngine."""

import pytest

from flagforge.cache import AsyncNullCache, NullCache
from flagforge.core.context import FeatureContext
from flagforge.core.engine import AsyncFlagEngine, FlagEngine
from flagforge.core.models import FlagDefinition, TenantOverride
from flagforge.storage.memory import AsyncInMemoryStorage, InMemoryStorage

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_engine() -> tuple[FlagEngine, InMemoryStorage]:
    storage = InMemoryStorage()
    engine = FlagEngine(storage=storage, cache=NullCache())
    return engine, storage


def ctx(
    tenant: str = "t1",
    user: str | None = None,
    env: str | None = None,
    groups: list[str] | None = None,
) -> FeatureContext:
    return FeatureContext(
        tenant_id=tenant,
        user_id=user,
        environment=env,
        group_ids=groups or [],
    )


# ---------------------------------------------------------------------------
# Basic evaluation
# ---------------------------------------------------------------------------


class TestIsEnabled:
    def test_unknown_flag_returns_false(self):
        engine, _ = make_engine()
        assert engine.is_enabled("nonexistent", ctx()) is False

    def test_default_disabled(self):
        engine, storage = make_engine()
        storage.upsert_definition(FlagDefinition(key="f", name="F", default_enabled=False))
        assert engine.is_enabled("f", ctx()) is False

    def test_default_enabled(self):
        engine, storage = make_engine()
        storage.upsert_definition(FlagDefinition(key="f", name="F", default_enabled=True))
        assert engine.is_enabled("f", ctx()) is True

    def test_tenant_id_required(self):
        engine, storage = make_engine()
        storage.upsert_definition(FlagDefinition(key="f", name="F", default_enabled=True))
        with pytest.raises(ValueError):
            engine.is_enabled("f", FeatureContext())


# ---------------------------------------------------------------------------
# Tenant overrides
# ---------------------------------------------------------------------------


class TestTenantOverride:
    def test_override_enable(self):
        engine, storage = make_engine()
        storage.upsert_definition(FlagDefinition(key="f", name="F", default_enabled=False))
        storage.upsert_tenant_override(TenantOverride(key="f", tenant_id="t1", enabled=True))
        assert engine.is_enabled("f", ctx("t1")) is True

    def test_override_disable(self):
        engine, storage = make_engine()
        storage.upsert_definition(FlagDefinition(key="f", name="F", default_enabled=True))
        storage.upsert_tenant_override(TenantOverride(key="f", tenant_id="t1", enabled=False))
        assert engine.is_enabled("f", ctx("t1")) is False

    def test_override_does_not_affect_other_tenant(self):
        engine, storage = make_engine()
        storage.upsert_definition(FlagDefinition(key="f", name="F", default_enabled=False))
        storage.upsert_tenant_override(TenantOverride(key="f", tenant_id="t1", enabled=True))
        assert engine.is_enabled("f", ctx("t2")) is False


# ---------------------------------------------------------------------------
# User targeting
# ---------------------------------------------------------------------------


class TestUserTargeting:
    def test_enabled_for_specific_user(self):
        engine, storage = make_engine()
        storage.upsert_definition(FlagDefinition(key="f", name="F", default_enabled=False))
        storage.upsert_tenant_override(
            TenantOverride(key="f", tenant_id="t1", enabled=False, enabled_for_users=["user_42"])
        )
        assert engine.is_enabled("f", ctx("t1", user="user_42")) is True
        assert engine.is_enabled("f", ctx("t1", user="user_99")) is False

    def test_enabled_for_group(self):
        engine, storage = make_engine()
        storage.upsert_definition(FlagDefinition(key="f", name="F", default_enabled=False))
        storage.upsert_tenant_override(
            TenantOverride(key="f", tenant_id="t1", enabled=False, enabled_for_groups=["beta"])
        )
        assert engine.is_enabled("f", ctx("t1", groups=["beta"])) is True
        assert engine.is_enabled("f", ctx("t1", groups=["standard"])) is False


# ---------------------------------------------------------------------------
# Environment gating
# ---------------------------------------------------------------------------


class TestEnvironmentGating:
    def test_flag_disabled_in_wrong_env(self):
        engine, storage = make_engine()
        storage.upsert_definition(
            FlagDefinition(
                key="f",
                name="F",
                default_enabled=True,
                environments=["staging", "production"],
            )
        )
        assert engine.is_enabled("f", ctx(env="dev")) is False
        assert engine.is_enabled("f", ctx(env="production")) is True

    def test_no_env_restriction(self):
        engine, storage = make_engine()
        storage.upsert_definition(FlagDefinition(key="f", name="F", default_enabled=True))
        assert engine.is_enabled("f", ctx(env=None)) is True
        assert engine.is_enabled("f", ctx(env="anything")) is True


# ---------------------------------------------------------------------------
# evaluate_many
# ---------------------------------------------------------------------------


class TestEvaluateMany:
    def test_evaluate_many(self):
        engine, storage = make_engine()
        storage.upsert_definition(FlagDefinition(key="a", name="A", default_enabled=True))
        storage.upsert_definition(FlagDefinition(key="b", name="B", default_enabled=False))
        result = engine.evaluate_many(["a", "b", "c"], ctx())
        assert result == {"a": True, "b": False, "c": False}

    def test_empty_keys_returns_empty(self):
        engine, _ = make_engine()
        # The engine itself accepts an empty list and returns {}
        result = engine.evaluate_many([], ctx())
        assert result == {}


# ---------------------------------------------------------------------------
# evaluate_all
# ---------------------------------------------------------------------------


class TestEvaluateAll:
    def test_evaluate_all(self):
        engine, storage = make_engine()
        storage.upsert_definition(FlagDefinition(key="a", name="A", default_enabled=True))
        storage.upsert_definition(FlagDefinition(key="b", name="B", default_enabled=False))
        storage.upsert_tenant_override(TenantOverride(key="b", tenant_id="t1", enabled=True))

        result = engine.evaluate_all(ctx("t1"))
        assert result == {"a": True, "b": True}

    def test_evaluate_all_tenant_isolation(self):
        engine, storage = make_engine()
        storage.upsert_definition(FlagDefinition(key="a", name="A", default_enabled=False))
        storage.upsert_tenant_override(TenantOverride(key="a", tenant_id="t1", enabled=True))
        storage.upsert_tenant_override(TenantOverride(key="a", tenant_id="t2", enabled=False))

        assert engine.evaluate_all(ctx("t1")) == {"a": True}
        assert engine.evaluate_all(ctx("t2")) == {"a": False}


# ---------------------------------------------------------------------------
# Caching
# ---------------------------------------------------------------------------


class MockCache(NullCache):
    def __init__(self):
        self.data = {}
        self.hits = 0
        self.sets = 0

    def get(self, key: str):
        if key in self.data:
            self.hits += 1
            return self.data[key]
        return None

    def set(self, key: str, value: bool, ttl: int | None = None):
        self.sets += 1
        self.data[key] = value


class TestCaching:
    def test_cache_hit_path(self):
        storage = InMemoryStorage()
        cache = MockCache()
        engine = FlagEngine(storage=storage, cache=cache)

        storage.upsert_definition(FlagDefinition(key="f", name="F", default_enabled=True))

        # First call - cache miss
        assert engine.is_enabled("f", ctx()) is True
        assert cache.hits == 0
        assert cache.sets == 1

        # Second call - cache hit
        assert engine.is_enabled("f", ctx()) is True
        assert cache.hits == 1
        assert cache.sets == 1

    def test_cache_key_includes_context(self):
        storage = InMemoryStorage()
        cache = MockCache()
        engine = FlagEngine(storage=storage, cache=cache)
        storage.upsert_definition(FlagDefinition(key="f", name="F", default_enabled=True))

        # Different users should have different cache keys
        engine.is_enabled("f", ctx(user="u1"))
        engine.is_enabled("f", ctx(user="u2"))

        assert cache.sets == 2
        assert cache.hits == 0


# ---------------------------------------------------------------------------
# Async engine
# ---------------------------------------------------------------------------


class TestAsyncFlagEngine:
    async def test_is_enabled_async(self):
        storage = AsyncInMemoryStorage()
        engine = AsyncFlagEngine(storage=storage, cache=AsyncNullCache())
        await storage.upsert_definition(FlagDefinition(key="f", name="F", default_enabled=True))
        result = await engine.is_enabled("f", ctx())
        assert result is True

    async def test_evaluate_many_async(self):
        storage = AsyncInMemoryStorage()
        engine = AsyncFlagEngine(storage=storage, cache=AsyncNullCache())
        await storage.upsert_definition(FlagDefinition(key="a", name="A", default_enabled=True))
        await storage.upsert_definition(FlagDefinition(key="b", name="B", default_enabled=False))
        result = await engine.evaluate_many(["a", "b"], ctx())
        assert result == {"a": True, "b": False}
