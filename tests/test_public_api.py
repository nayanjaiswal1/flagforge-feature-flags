import pytest

import flagforge
from flagforge.core.context import FeatureContext
from flagforge.core.engine import FlagEngine
from flagforge.core.models import FlagDefinition
from flagforge.storage.memory import InMemoryStorage


def test_public_api_sync():
    storage = InMemoryStorage()
    storage.upsert_definition(FlagDefinition(key="f1", name="F1", default_enabled=True))
    engine = FlagEngine(storage=storage)

    flagforge.configure_engine(engine)
    assert flagforge.get_engine() == engine

    ctx = FeatureContext(tenant_id="t1")
    assert flagforge.is_enabled("f1", ctx) is True
    assert flagforge.evaluate_many(["f1"], ctx) == {"f1": True}


def test_public_api_errors():
    # No engine configured
    flagforge._global_engine = None  # Reset
    ctx = FeatureContext(tenant_id="t1")

    with pytest.raises(RuntimeError, match="Configure the engine"):
        flagforge.is_enabled("f1", ctx)

    with pytest.raises(ValueError, match="empty"):
        flagforge.is_enabled("", ctx)


@pytest.mark.asyncio
async def test_public_api_async_error():
    from flagforge.core.engine import AsyncFlagEngine
    from flagforge.storage.memory import AsyncInMemoryStorage

    engine = AsyncFlagEngine(storage=AsyncInMemoryStorage())
    flagforge.configure_engine(engine)

    ctx = FeatureContext(tenant_id="t1")
    # Calling sync is_enabled on async engine should fail
    with pytest.raises(RuntimeError, match="Use 'async is_enabled\\(\\)'"):
        flagforge.is_enabled("f1", ctx)
