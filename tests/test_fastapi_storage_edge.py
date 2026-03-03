import pytest
from sqlalchemy import text

from flagforge.contrib.fastapi.storage import AsyncSQLAlchemyStorage

DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.mark.asyncio
async def test_fastapi_storage_corrupted_json():
    storage = AsyncSQLAlchemyStorage(DATABASE_URL)
    await storage.init_db()

    # Insert corrupted JSON manually
    async with storage.engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO feature_flag_definitions "
                "(key, name, description, default_enabled, is_public, rollout_percentage, deprecated, environments) "
                "VALUES (:key, :name, :desc, :de, :ip, :rp, :dep, :envs)"
            ),
            {
                "key": "bad_json",
                "name": "Bad",
                "desc": "",
                "de": False,
                "ip": False,
                "rp": 0,
                "dep": False,
                "envs": "{invalid",
            },
        )

        await conn.execute(
            text(
                "INSERT INTO tenant_overrides (flag_key, tenant_id, enabled, enabled_for_users) VALUES (:key, :tid, :en, :users)"
            ),
            {"key": "bad_json", "tid": "t1", "en": True, "users": "{invalid"},
        )

    # Read back - should handle error gracefully
    defn = await storage.get_definition("bad_json")
    assert defn.environments is None

    override = await storage.get_tenant_override("bad_json", "t1")
    assert override.enabled_for_users == []

    await storage.close()
