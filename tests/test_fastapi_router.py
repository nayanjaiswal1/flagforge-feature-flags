from fastapi import FastAPI
import pytest

from flagforge.cache.null import AsyncNullCache
from flagforge.contrib.fastapi.dependencies import get_engine, get_storage
from flagforge.contrib.fastapi.router import router
from flagforge.contrib.fastapi.storage import AsyncSQLAlchemyStorage
from flagforge.core.engine import AsyncFlagEngine

DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def app():
    app = FastAPI()
    app.include_router(router)

    storage = AsyncSQLAlchemyStorage(DATABASE_URL)
    await storage.init_db()

    engine = AsyncFlagEngine(storage=storage, cache=AsyncNullCache())

    # Override dependencies
    app.dependency_overrides[get_storage] = lambda: storage
    app.dependency_overrides[get_engine] = lambda: engine

    yield app
    await storage.close()


@pytest.mark.asyncio
async def test_fastapi_router_flow():
    from httpx import ASGITransport, AsyncClient

    app = FastAPI()
    app.include_router(router)

    storage = AsyncSQLAlchemyStorage(DATABASE_URL)
    await storage.init_db()
    engine = AsyncFlagEngine(storage=storage, cache=AsyncNullCache())

    app.state.flagforge_storage = storage
    app.state.flagforge_engine = engine

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Create a flag via admin
        resp = await ac.post(
            "/flags/admin/",
            json={
                "key": "f1",
                "name": "F1",
                "is_public": True,
                "default_enabled": True,
            },
        )
        assert resp.status_code == 200

        # 2. List flags (no tenant -> empty)
        resp = await ac.get("/flags/")
        assert resp.json() == {}

        # 3. List flags with tenant
        resp = await ac.get("/flags/", headers={"X-Tenant-ID": "t1"})
        assert resp.status_code == 200
        assert "f1" in resp.json()
        assert resp.json()["f1"] is True

        # 4. Create override
        resp = await ac.put("/flags/admin/f1/tenants/t1/", json={"enabled": False})
        assert resp.status_code == 200

        # 5. List flags again -> should be False now
        resp = await ac.get("/flags/", headers={"X-Tenant-ID": "t1", "X-User-ID": "u1"})
        assert resp.json()["f1"] is False

    await storage.close()
