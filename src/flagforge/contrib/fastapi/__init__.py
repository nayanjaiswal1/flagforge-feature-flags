"""FastAPI integration for FlagForge."""

from .context import context_factory
from .dependencies import feature_flag_dependency, get_engine, get_storage
from .lifespan import create_flagforge_lifespan, flagforge_lifespan
from .middleware import FlagForgeMiddleware
from .models import Base, FlagDefinition, TenantOverride
from .router import router
from .storage import AsyncSQLAlchemyStorage

__all__ = [
    "AsyncSQLAlchemyStorage",
    "Base",
    "FlagDefinition",
    "FlagForgeMiddleware",
    "TenantOverride",
    "context_factory",
    "create_flagforge_lifespan",
    "feature_flag_dependency",
    "flagforge_lifespan",
    "get_engine",
    "get_storage",
    "router",
]
