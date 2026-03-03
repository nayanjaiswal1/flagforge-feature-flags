import pytest

from flagforge.core.models import FlagDefinition, TenantOverride
from flagforge.storage.memory import AsyncInMemoryStorage, InMemoryStorage


def test_memory_storage_definitions():
    storage = InMemoryStorage()
    f1 = FlagDefinition(key="f1", name="F1")
    f2 = FlagDefinition(key="f2", name="F2")

    storage.upsert_definition(f1)
    storage.upsert_definition(f2)

    assert storage.get_definition("f1") == f1
    assert storage.get_definition("f2") == f2
    assert len(storage.get_all_definitions()) == 2

    storage.delete_definition("f1")
    assert storage.get_definition("f1") is None
    assert len(storage.get_all_definitions()) == 1

def test_memory_storage_overrides():
    storage = InMemoryStorage()
    o1 = TenantOverride(key="f1", tenant_id="t1", enabled=True)
    o2 = TenantOverride(key="f1", tenant_id="t2", enabled=False)
    o3 = TenantOverride(key="f2", tenant_id="t1", enabled=True)

    storage.upsert_tenant_override(o1)
    storage.upsert_tenant_override(o2)
    storage.upsert_tenant_override(o3)

    assert storage.get_tenant_override("f1", "t1") == o1
    assert storage.get_tenant_override("f1", "t2") == o2

    t1_overrides = storage.get_all_tenant_overrides("t1")
    assert len(t1_overrides) == 2
    assert o1 in t1_overrides
    assert o3 in t1_overrides

    storage.delete_tenant_override("f1", "t1")
    assert storage.get_tenant_override("f1", "t1") is None

@pytest.mark.asyncio
async def test_async_memory_storage():
    storage = AsyncInMemoryStorage()
    f1 = FlagDefinition(key="f1", name="F1")
    o1 = TenantOverride(key="f1", tenant_id="t1", enabled=True)

    await storage.upsert_definition(f1)
    await storage.upsert_tenant_override(o1)

    assert await storage.get_definition("f1") == f1
    assert (await storage.get_all_definitions()) == [f1]
    assert await storage.get_tenant_override("f1", "t1") == o1
    assert (await storage.get_all_tenant_overrides("t1")) == [o1]

    await storage.delete_definition("f1")
    assert await storage.get_definition("f1") is None

    await storage.delete_tenant_override("f1", "t1")
    assert await storage.get_tenant_override("f1", "t1") is None
