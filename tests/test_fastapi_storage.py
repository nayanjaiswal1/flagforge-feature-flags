import pytest
import pytest_asyncio

from flagforge.contrib.fastapi.storage import AsyncSQLAlchemyStorage
from flagforge.core.models import FlagDefinition, TenantOverride

DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def storage():
    storage = AsyncSQLAlchemyStorage(DATABASE_URL)
    await storage.init_db()
    yield storage
    await storage.close()


@pytest.mark.asyncio
async def test_fastapi_storage_definitions(storage):
    d1 = FlagDefinition(key="f1", name="F1", default_enabled=True)
    await storage.upsert_definition(d1)

    retrieved = await storage.get_definition("f1")
    assert retrieved.key == "f1"
    assert retrieved.default_enabled is True

    all_defs = await storage.get_all_definitions()
    assert len(all_defs) == 1

    await storage.delete_definition("f1")
    assert await storage.get_definition("f1") is None


@pytest.mark.asyncio
async def test_fastapi_storage_overrides(storage):
    d1 = FlagDefinition(key="f1", name="F1")
    await storage.upsert_definition(d1)

    o1 = TenantOverride(key="f1", tenant_id="t1", enabled=True)
    await storage.upsert_tenant_override(o1)

    retrieved = await storage.get_tenant_override("f1", "t1")
    assert retrieved.enabled is True

    all_t1 = await storage.get_all_tenant_overrides("t1")
    assert len(all_t1) == 1

    await storage.delete_tenant_override("f1", "t1")
    assert await storage.get_tenant_override("f1", "t1") is None
