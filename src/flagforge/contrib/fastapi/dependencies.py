"""FastAPI dependencies for FlagForge."""

from fastapi import Depends, HTTPException, Request

from flagforge.core.context import FeatureContext
from flagforge.core.engine import AsyncFlagEngine

from .context import context_factory
from .storage import AsyncSQLAlchemyStorage


def get_engine(request: Request) -> AsyncFlagEngine:
    """Get the AsyncFlagEngine from app state.

    Args:
        request: FastAPI request

    Returns:
        AsyncFlagEngine instance

    Raises:
        HTTPException: If engine not configured
    """
    engine: AsyncFlagEngine | None = getattr(request.app.state, "flagforge_engine", None)
    if engine is None:
        raise HTTPException(
            status_code=500,
            detail="FlagForge engine not configured. Add flagforge_engine to app.state.",
        )
    return engine


def get_storage(request: Request) -> AsyncSQLAlchemyStorage:
    """Get the AsyncSQLAlchemyStorage from app state.

    Args:
        request: FastAPI request

    Returns:
        AsyncSQLAlchemyStorage instance

    Raises:
        HTTPException: If storage not configured
    """
    storage: AsyncSQLAlchemyStorage | None = getattr(request.app.state, "flagforge_storage", None)
    if storage is None:
        raise HTTPException(
            status_code=500,
            detail="FlagForge storage not configured. Add flagforge_storage to app.state.",
        )
    return storage


async def get_context(request: Request) -> FeatureContext:
    """Get the FeatureContext for the current request.

    Args:
        request: FastAPI request

    Returns:
        FeatureContext from request
    """
    return context_factory(request)


def feature_flag_dependency(flag_key: str):
    """Dependency factory for requiring a feature flag to be enabled.

    Args:
        flag_key: The feature flag key to check

    Returns:
        FastAPI dependency that requires the flag to be enabled

    Example:
        @app.get("/features")
        async def get_features(flag: bool = Depends(feature_flag_dependency("my_feature"))):
            ...
    """

    async def dependency(
        engine: AsyncFlagEngine = Depends(get_engine),
        context: FeatureContext = Depends(get_context),
    ) -> bool:
        is_enabled = await engine.is_enabled(flag_key, context)
        if not is_enabled:
            raise HTTPException(
                status_code=404,
                detail=f"Feature flag '{flag_key}' is not enabled",
            )
        return True

    return dependency


def get_request_context() -> FeatureContext:
    """Get the current request's FeatureContext.

    This is a simple dependency that returns the context from state.
    """
    return FeatureContext()
