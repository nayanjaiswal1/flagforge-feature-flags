"""FastAPI lifespan handler for FlagForge."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from flagforge.cache import AsyncLocalCache
from flagforge.core.engine import AsyncFlagEngine

from .storage import AsyncSQLAlchemyStorage


@asynccontextmanager
async def flagforge_lifespan(
    app: FastAPI,
    database_url: str,
    echo: bool = False,
) -> AsyncGenerator[None, None]:
    """Lifespan context manager for FlagForge FastAPI integration.

    This initializes the storage and engine on app startup and validates
    connectivity. It also ensures proper cleanup on shutdown.

    Args:
        app: FastAPI application
        database_url: Database connection URL
        echo: Whether to echo SQL queries

    Yields:
        None
    """
    storage: AsyncSQLAlchemyStorage | None = None
    engine: AsyncFlagEngine | None = None

    try:
        storage = AsyncSQLAlchemyStorage(database_url=database_url, echo=echo)
        await storage.init_db()

        engine = AsyncFlagEngine(storage=storage, cache=AsyncLocalCache())

        app.state.flagforge_storage = storage
        app.state.flagforge_engine = engine

        yield

    except Exception as e:
        raise RuntimeError(
            f"FlagForge initialization failed: {e}. "
            "Ensure database is reachable and settings are valid."
        ) from e

    finally:
        if storage:
            await storage.close()


def create_flagforge_lifespan(database_url: str, echo: bool = False):
    """Factory to create a FlagForge lifespan context manager.

    Args:
        database_url: Database connection URL
        echo: Whether to echo SQL queries

    Returns:
        Lifespan context manager function
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        storage: AsyncSQLAlchemyStorage | None = None
        engine: AsyncFlagEngine | None = None

        try:
            storage = AsyncSQLAlchemyStorage(database_url=database_url, echo=echo)
            await storage.init_db()

            engine = AsyncFlagEngine(storage=storage, cache=AsyncLocalCache())

            app.state.flagforge_storage = storage
            app.state.flagforge_engine = engine

            yield

        except Exception as e:
            raise RuntimeError(
                f"FlagForge initialization failed: {e}. "
                "Ensure database is reachable and settings are valid."
            ) from e

        finally:
            if storage:
                await storage.close()

    return lifespan
