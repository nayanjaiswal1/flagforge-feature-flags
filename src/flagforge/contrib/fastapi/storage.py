"""FastAPI async storage backend for FlagForge using SQLAlchemy."""

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from flagforge.core.models import FlagDefinition, TenantOverride
from flagforge.storage.base import AsyncStorageBackend

from .models import (
    Base,
)
from .models import (
    FlagDefinition as ORMFlagDefinition,
)
from .models import (
    TenantOverride as ORMTenantOverride,
)


class AsyncSQLAlchemyStorage(AsyncStorageBackend):
    """Async SQLAlchemy storage backend for feature flags.

    Supports both column-based and schema-based multi-tenancy.
    """

    def __init__(
        self,
        database_url: str,
        echo: bool = False,
        pool_size: int | None = None,
        max_overflow: int | None = None,
    ):
        """Initialize async SQLAlchemy storage.

        Args:
            database_url: Database connection URL (e.g., postgresql+asyncpg://...)
            echo: Whether to echo SQL queries
            pool_size: Connection pool size
            max_overflow: Max overflow connections
        """
        self.database_url = database_url

        # Build kwargs, avoiding arguments not supported by SQLite
        engine_kwargs: dict[str, Any] = {"echo": echo}
        if "sqlite" not in database_url:
            if pool_size is not None:
                engine_kwargs["pool_size"] = pool_size
            if max_overflow is not None:
                engine_kwargs["max_overflow"] = max_overflow

        self.engine = create_async_engine(database_url, **engine_kwargs)
        self.async_session = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init_db(self):
        """Initialize database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self):
        """Close database connection."""
        await self.engine.dispose()

    async def get_definition(self, key: str) -> FlagDefinition | None:
        """Get a flag definition by key."""
        async with self.async_session() as session:
            result = await session.execute(
                select(ORMFlagDefinition).where(ORMFlagDefinition.key == key)
            )
            orm_obj = result.scalar_one_or_none()
            if orm_obj is None:
                return None
            return self._to_flag_definition(orm_obj)

    async def get_all_definitions(self) -> list[FlagDefinition]:
        """Get all flag definitions."""
        async with self.async_session() as session:
            result = await session.execute(select(ORMFlagDefinition))
            orm_objs = result.scalars().all()
            return [self._to_flag_definition(obj) for obj in orm_objs]

    async def get_tenant_override(self, key: str, tenant_id: str) -> TenantOverride | None:
        """Get tenant-specific override for a flag."""
        async with self.async_session() as session:
            result = await session.execute(
                select(ORMTenantOverride)
                .where(ORMTenantOverride.flag_key == key)
                .where(ORMTenantOverride.tenant_id == tenant_id)
            )
            orm_obj = result.scalar_one_or_none()
            if orm_obj is None:
                return None
            return self._to_tenant_override(orm_obj)

    async def get_all_tenant_overrides(self, tenant_id: str) -> list[TenantOverride]:
        """Get all overrides for a tenant."""
        async with self.async_session() as session:
            result = await session.execute(
                select(ORMTenantOverride).where(ORMTenantOverride.tenant_id == tenant_id)
            )
            orm_objs = result.scalars().all()
            return [self._to_tenant_override(obj) for obj in orm_objs]

    async def upsert_definition(self, defn: FlagDefinition) -> None:
        """Create or update a flag definition."""
        async with self.async_session() as session:
            result = await session.execute(
                select(ORMFlagDefinition).where(ORMFlagDefinition.key == defn.key)
            )
            orm_obj = result.scalar_one_or_none()

            if orm_obj:
                orm_obj.name = defn.name
                orm_obj.description = defn.description
                orm_obj.default_enabled = defn.default_enabled
                orm_obj.is_public = defn.is_public
                orm_obj.rollout_percentage = defn.rollout_percentage
                orm_obj.deprecated = defn.deprecated
                orm_obj.environments = json.dumps(defn.environments) if defn.environments else None
            else:
                orm_obj = ORMFlagDefinition(
                    key=defn.key,
                    name=defn.name,
                    description=defn.description,
                    default_enabled=defn.default_enabled,
                    is_public=defn.is_public,
                    rollout_percentage=defn.rollout_percentage,
                    deprecated=defn.deprecated,
                    environments=json.dumps(defn.environments) if defn.environments else None,
                )
                session.add(orm_obj)

            await session.commit()

    async def upsert_tenant_override(self, override: TenantOverride) -> None:
        """Create or update a tenant override."""
        async with self.async_session() as session:
            result = await session.execute(
                select(ORMTenantOverride)
                .where(ORMTenantOverride.flag_key == override.key)
                .where(ORMTenantOverride.tenant_id == override.tenant_id)
            )
            orm_obj = result.scalar_one_or_none()

            if orm_obj:
                orm_obj.enabled = override.enabled
                orm_obj.rollout_percentage = override.rollout_percentage
                orm_obj.enabled_for_users = json.dumps(override.enabled_for_users)
                orm_obj.enabled_for_groups = json.dumps(override.enabled_for_groups)
                orm_obj.updated_by = override.updated_by
            else:
                orm_obj = ORMTenantOverride(
                    flag_key=override.key,
                    tenant_id=override.tenant_id,
                    enabled=override.enabled,
                    rollout_percentage=override.rollout_percentage,
                    enabled_for_users=json.dumps(override.enabled_for_users),
                    enabled_for_groups=json.dumps(override.enabled_for_groups),
                    updated_by=override.updated_by,
                )
                session.add(orm_obj)

            await session.commit()

    async def delete_tenant_override(self, key: str, tenant_id: str) -> None:
        """Delete a tenant override."""
        async with self.async_session() as session:
            result = await session.execute(
                select(ORMTenantOverride)
                .where(ORMTenantOverride.flag_key == key)
                .where(ORMTenantOverride.tenant_id == tenant_id)
            )
            orm_obj = result.scalar_one_or_none()
            if orm_obj:
                await session.delete(orm_obj)
                await session.commit()

    async def delete_definition(self, key: str) -> None:
        """Delete a flag definition and all its tenant overrides."""
        async with self.async_session() as session:
            result = await session.execute(
                select(ORMFlagDefinition).where(ORMFlagDefinition.key == key)
            )
            orm_obj = result.scalar_one_or_none()
            if orm_obj:
                await session.delete(orm_obj)
                await session.commit()

    def _to_flag_definition(self, obj: ORMFlagDefinition) -> FlagDefinition:
        """Convert ORM model to FlagDefinition."""
        envs_raw = obj.environments
        envs: list[str] | None = None
        if envs_raw:
            try:
                decoded = json.loads(envs_raw)
                if isinstance(decoded, list):
                    envs = decoded
            except (json.JSONDecodeError, TypeError):
                envs = None

        return FlagDefinition(
            key=obj.key,
            name=obj.name,
            description=obj.description,
            default_enabled=obj.default_enabled,
            is_public=obj.is_public,
            rollout_percentage=obj.rollout_percentage,
            deprecated=obj.deprecated,
            environments=envs,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )

    def _to_tenant_override(self, obj: ORMTenantOverride) -> TenantOverride:
        """Convert ORM model to TenantOverride."""

        def parse_json(val):
            if val is None:
                return []
            try:
                return json.loads(val)
            except (json.JSONDecodeError, TypeError):
                return []

        return TenantOverride(
            key=obj.flag_key,
            tenant_id=obj.tenant_id,
            enabled=obj.enabled,
            rollout_percentage=obj.rollout_percentage,
            enabled_for_users=parse_json(obj.enabled_for_users),
            enabled_for_groups=parse_json(obj.enabled_for_groups),
            updated_at=obj.updated_at,
            updated_by=obj.updated_by,
        )
