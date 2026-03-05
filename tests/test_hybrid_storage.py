"""Tests for hybrid tenancy mode storage."""

from django.test import override_settings
import pytest

from flagforge.contrib.django.models import (
    FeatureFlagDefinition,
    TenantFeatureFlag,
    TenantFlagOverride,
)
from flagforge.contrib.django.storage import DjangoStorage
from flagforge.core.exceptions import StorageError
from flagforge.core.models import FlagDefinition, TenantOverride

# ---------------------------------------------------------------------------
# DjangoStorage: 'hybrid' is now a valid mode
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_hybrid_mode_is_valid():
    storage = DjangoStorage(tenancy_mode="hybrid")
    assert storage.tenancy_mode == "hybrid"


def test_invalid_mode_still_raises():
    with pytest.raises(StorageError):
        DjangoStorage(tenancy_mode="bad_mode")


# ---------------------------------------------------------------------------
# Definitions still work the same way in hybrid mode
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_hybrid_definitions_crud():
    storage = DjangoStorage(tenancy_mode="hybrid")

    defn = FlagDefinition(key="feat_x", name="Feature X", default_enabled=True)
    storage.upsert_definition(defn)

    assert FeatureFlagDefinition.objects.filter(key="feat_x").exists()

    retrieved = storage.get_definition("feat_x")
    assert retrieved.key == "feat_x"
    assert retrieved.default_enabled is True

    assert len(storage.get_all_definitions()) >= 1

    storage.delete_definition("feat_x")
    assert not FeatureFlagDefinition.objects.filter(key="feat_x").exists()


# ---------------------------------------------------------------------------
# Hybrid mode overrides use TenantFlagOverride (no tenant_id column)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_hybrid_upsert_and_get_override():
    storage = DjangoStorage(tenancy_mode="hybrid")

    # Create definition first
    storage.upsert_definition(FlagDefinition(key="feat_a", name="Feat A"))

    # Upsert a hybrid override — tenant_id comes from context, not stored
    override = TenantOverride(key="feat_a", tenant_id="tenant-x", enabled=True)
    storage.upsert_tenant_override(override)

    # Should have created a TenantFlagOverride row (no tenant_id column)
    assert TenantFlagOverride.objects.filter(key__key="feat_a").exists()
    row = TenantFlagOverride.objects.get(key__key="feat_a")
    assert row.enabled is True

    # Should NOT have created a TenantFeatureFlag row
    assert not TenantFeatureFlag.objects.filter(key__key="feat_a").exists()

    # Retrieve — tenant_id is injected from the call, not from DB
    retrieved = storage.get_tenant_override("feat_a", "tenant-x")
    assert retrieved is not None
    assert retrieved.enabled is True
    assert retrieved.tenant_id == "tenant-x"
    assert retrieved.key == "feat_a"


@pytest.mark.django_db
def test_hybrid_get_all_overrides():
    storage = DjangoStorage(tenancy_mode="hybrid")

    storage.upsert_definition(FlagDefinition(key="feat_b", name="Feat B"))
    storage.upsert_definition(FlagDefinition(key="feat_c", name="Feat C"))

    storage.upsert_tenant_override(TenantOverride(key="feat_b", tenant_id="t1", enabled=True))
    storage.upsert_tenant_override(TenantOverride(key="feat_c", tenant_id="t1", enabled=False))

    overrides = storage.get_all_tenant_overrides("t1")
    assert len(overrides) == 2
    keys = {o.key for o in overrides}
    assert keys == {"feat_b", "feat_c"}
    # tenant_id injected correctly for all rows
    for o in overrides:
        assert o.tenant_id == "t1"


@pytest.mark.django_db
def test_hybrid_delete_override():
    storage = DjangoStorage(tenancy_mode="hybrid")

    storage.upsert_definition(FlagDefinition(key="feat_d", name="Feat D"))
    storage.upsert_tenant_override(TenantOverride(key="feat_d", tenant_id="t1", enabled=True))
    assert TenantFlagOverride.objects.filter(key__key="feat_d").exists()

    storage.delete_tenant_override("feat_d", "t1")
    assert not TenantFlagOverride.objects.filter(key__key="feat_d").exists()


@pytest.mark.django_db
def test_hybrid_get_nonexistent_override_returns_none():
    storage = DjangoStorage(tenancy_mode="hybrid")
    storage.upsert_definition(FlagDefinition(key="feat_e", name="Feat E"))

    result = storage.get_tenant_override("feat_e", "t1")
    assert result is None


@pytest.mark.django_db
def test_hybrid_upsert_is_idempotent():
    storage = DjangoStorage(tenancy_mode="hybrid")
    storage.upsert_definition(FlagDefinition(key="feat_f", name="Feat F"))

    storage.upsert_tenant_override(TenantOverride(key="feat_f", tenant_id="t1", enabled=True))
    storage.upsert_tenant_override(TenantOverride(key="feat_f", tenant_id="t1", enabled=False))

    # Still only one row
    assert TenantFlagOverride.objects.filter(key__key="feat_f").count() == 1
    row = TenantFlagOverride.objects.get(key__key="feat_f")
    assert row.enabled is False


# ---------------------------------------------------------------------------
# Hybrid mode: full engine evaluation
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@override_settings(FLAGFORGE_TENANCY_MODE="hybrid")
def test_hybrid_engine_evaluation(monkeypatch):
    monkeypatch.setattr("flagforge.contrib.django.engine._engine", None)

    from flagforge.cache.null import NullCache
    from flagforge.contrib.django.storage import DjangoStorage
    from flagforge.core.context import FeatureContext
    from flagforge.core.engine import FlagEngine

    storage = DjangoStorage(tenancy_mode="hybrid")
    engine = FlagEngine(storage=storage, cache=NullCache())

    # Create a flag that defaults to False
    storage.upsert_definition(FlagDefinition(key="feat_g", name="Feat G", default_enabled=False))

    # No override yet → disabled
    ctx = FeatureContext(tenant_id="tenant-y")
    assert engine.is_enabled("feat_g", ctx) is False

    # Enable it via hybrid override
    storage.upsert_tenant_override(TenantOverride(key="feat_g", tenant_id="tenant-y", enabled=True))
    assert engine.is_enabled("feat_g", ctx) is True


# ---------------------------------------------------------------------------
# Column mode still works (regression)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_column_mode_unaffected():
    storage = DjangoStorage(tenancy_mode="column")
    storage.upsert_definition(FlagDefinition(key="feat_h", name="Feat H"))
    storage.upsert_tenant_override(
        TenantOverride(key="feat_h", tenant_id="col_tenant", enabled=True)
    )

    assert TenantFeatureFlag.objects.filter(key__key="feat_h", tenant_id="col_tenant").exists()
    assert not TenantFlagOverride.objects.filter(key__key="feat_h").exists()

    o = storage.get_tenant_override("feat_h", "col_tenant")
    assert o.enabled is True
    assert o.tenant_id == "col_tenant"


# ---------------------------------------------------------------------------
# check_tenancy_mode accepts 'hybrid'
# ---------------------------------------------------------------------------


@override_settings(FLAGFORGE_TENANCY_MODE="hybrid")
def test_check_accepts_hybrid():
    from flagforge.contrib.django.checks import check_tenancy_mode

    assert check_tenancy_mode(None) == []


@override_settings(FLAGFORGE_TENANCY_MODE="invalid")
def test_check_rejects_invalid():
    from flagforge.contrib.django.checks import check_tenancy_mode

    errors = check_tenancy_mode(None)
    assert len(errors) == 1
    assert errors[0].id == "flagforge.E001"
