from fastapi import FastAPI
import pytest

from flagforge.contrib.fastapi.lifespan import create_flagforge_lifespan, flagforge_lifespan


@pytest.mark.asyncio
async def test_lifespan_success():
    app = FastAPI()
    async with flagforge_lifespan(app, "sqlite+aiosqlite:///:memory:"):
        assert app.state.flagforge_storage is not None
        assert app.state.flagforge_engine is not None

        # Verify engine uses the storage
        assert app.state.flagforge_engine.storage is app.state.flagforge_storage


@pytest.mark.asyncio
async def test_lifespan_factory():
    app = FastAPI()
    lifespan = create_flagforge_lifespan("sqlite+aiosqlite:///:memory:")

    async with lifespan(app):
        assert app.state.flagforge_storage is not None
        assert app.state.flagforge_engine is not None


@pytest.mark.asyncio
async def test_lifespan_error():
    app = FastAPI()
    # Invalid DB URL should raise RuntimeError
    # SQLAlchemy might not validate URL immediately in constructor but init_db might fail?
    # Actually create_async_engine might fail if driver not found.

    with pytest.raises(RuntimeError, match="FlagForge initialization failed"):
        async with flagforge_lifespan(app, "invalid://db"):
            pass
