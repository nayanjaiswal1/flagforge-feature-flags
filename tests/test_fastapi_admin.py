from unittest.mock import AsyncMock, Mock

import pytest

from flagforge.contrib.fastapi.router import delete_tenant_override
from flagforge.contrib.fastapi.storage import AsyncSQLAlchemyStorage


@pytest.mark.asyncio
async def test_admin_delete_override():
    storage = Mock(spec=AsyncSQLAlchemyStorage)
    storage.delete_tenant_override = AsyncMock()

    result = await delete_tenant_override("f1", "t1", storage)

    storage.delete_tenant_override.assert_awaited_with("f1", "t1")
    assert result == {"status": "deleted", "key": "f1", "tenant_id": "t1"}
