import pytest

from flagforge.contrib.django.models import FeatureFlagDefinition, TenantFeatureFlag
from flagforge.contrib.django.storage import DjangoStorageAdapter
from flagforge.core.models import FlagDefinition, TenantOverride


@pytest.mark.django_db
def test_django_storage_definitions():
    adapter = DjangoStorageAdapter()
    d1 = FlagDefinition(key="f1", name="F1", default_enabled=True)

    adapter.upsert_definition(d1)

    # Verify in DB
    assert FeatureFlagDefinition.objects.filter(key="f1").exists()

    # Verify via adapter
    retrieved = adapter.get_definition("f1")
    assert retrieved.key == "f1"
    assert retrieved.default_enabled is True

    assert len(adapter.get_all_definitions()) == 1

    adapter.delete_definition("f1")
    assert not FeatureFlagDefinition.objects.filter(key="f1").exists()


@pytest.mark.django_db
def test_django_storage_overrides():
    adapter = DjangoStorageAdapter()
    d1 = FlagDefinition(key="f1", name="F1")
    adapter.upsert_definition(d1)

    o1 = TenantOverride(key="f1", tenant_id="t1", enabled=True)
    adapter.upsert_tenant_override(o1)

    # Verify in DB
    assert TenantFeatureFlag.objects.filter(tenant_id="t1", key__key="f1").exists()

    # Verify via adapter
    retrieved = adapter.get_tenant_override("f1", "t1")
    assert retrieved.enabled is True

    all_t1 = adapter.get_all_tenant_overrides("t1")
    assert len(all_t1) == 1
    assert all_t1[0].key == "f1"

    adapter.delete_tenant_override("f1", "t1")
    assert not TenantFeatureFlag.objects.filter(tenant_id="t1", key__key="f1").exists()


@pytest.mark.django_db
def test_django_storage_invalid_mode():
    from flagforge.contrib.django.storage import DjangoStorage
    from flagforge.core.exceptions import StorageError

    with pytest.raises(StorageError):
        DjangoStorage(tenancy_mode="invalid")
