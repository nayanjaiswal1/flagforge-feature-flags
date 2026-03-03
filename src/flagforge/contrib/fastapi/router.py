"""FastAPI router for FlagForge API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from flagforge.core.engine import AsyncFlagEngine

from .dependencies import get_engine, get_storage
from .storage import AsyncSQLAlchemyStorage

router = APIRouter(prefix="/flags", tags=["feature-flags"])


class FlagResponse(BaseModel):
    key: str
    enabled: bool


class FlagDefinitionInput(BaseModel):
    key: str
    name: str
    description: str = ""
    default_enabled: bool = False
    is_public: bool = False
    rollout_percentage: int = 0
    deprecated: bool = False
    environments: list[str] | None = None


class TenantOverrideInput(BaseModel):
    enabled: bool | None = None
    rollout_percentage: int | None = None
    enabled_for_users: list[str] = []
    enabled_for_groups: list[str] = []
    updated_by: str | None = None


@router.get("/", response_model=dict[str, bool])
async def list_flags(
    request: Request,
    engine: AsyncFlagEngine = Depends(get_engine),
):
    """List all resolved flags for the current user/tenant.

    Authenticated users see all flags; anonymous users see only public flags.
    """
    from .context import context_factory

    context = context_factory(request)

    if context.tenant_id is None:
        return {}

    if context.user_id:
        return await engine.evaluate_all(context)
    else:
        storage = get_storage(request)
        public_flags = await storage.get_all_definitions()
        public_keys = [f.key for f in public_flags if f.is_public]
        return await engine.evaluate_many(public_keys, context)


@router.get("/admin/", response_model=list[dict])
async def admin_list_flags(
    engine: AsyncFlagEngine = Depends(get_engine),
    storage: AsyncSQLAlchemyStorage = Depends(get_storage),
):
    """List all raw flag definitions (admin only)."""
    flags = await storage.get_all_definitions()
    return [
        {
            "key": f.key,
            "name": f.name,
            "description": f.description,
            "default_enabled": f.default_enabled,
            "is_public": f.is_public,
            "rollout_percentage": f.rollout_percentage,
            "deprecated": f.deprecated,
            "environments": f.environments,
        }
        for f in flags
    ]


@router.post("/admin/")
async def admin_create_flag(
    data: FlagDefinitionInput,
    storage: AsyncSQLAlchemyStorage = Depends(get_storage),
):
    """Create a new flag definition (admin only)."""
    from flagforge.core.models import FlagDefinition

    defn = FlagDefinition(
        key=data.key,
        name=data.name,
        description=data.description,
        default_enabled=data.default_enabled,
        is_public=data.is_public,
        rollout_percentage=data.rollout_percentage,
        deprecated=data.deprecated,
        environments=data.environments,
    )
    await storage.upsert_definition(defn)
    return {"status": "created", "key": data.key}


@router.put("/admin/{key}/")
async def admin_update_flag(
    key: str,
    data: FlagDefinitionInput,
    storage: AsyncSQLAlchemyStorage = Depends(get_storage),
):
    """Update a flag definition (admin only)."""
    existing = await storage.get_definition(key)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"Flag '{key}' not found")

    from flagforge.core.models import FlagDefinition

    defn = FlagDefinition(
        key=key,
        name=data.name,
        description=data.description,
        default_enabled=data.default_enabled,
        is_public=data.is_public,
        rollout_percentage=data.rollout_percentage,
        deprecated=data.deprecated,
        environments=data.environments,
    )
    await storage.upsert_definition(defn)
    return {"status": "updated", "key": key}


@router.delete("/admin/{key}/")
async def admin_delete_flag(
    key: str,
    storage: AsyncSQLAlchemyStorage = Depends(get_storage),
):
    """Delete a flag definition (admin only)."""
    await storage.delete_definition(key)
    return {"status": "deleted", "key": key}


@router.put("/admin/{key}/tenants/{tenant_id}/")
async def admin_upsert_override(
    key: str,
    tenant_id: str,
    data: TenantOverrideInput,
    storage: AsyncSQLAlchemyStorage = Depends(get_storage),
):
    """Upsert a tenant override (admin only)."""
    from flagforge.core.models import TenantOverride

    override = TenantOverride(
        key=key,
        tenant_id=tenant_id,
        enabled=data.enabled,
        rollout_percentage=data.rollout_percentage,
        enabled_for_users=data.enabled_for_users,
        enabled_for_groups=data.enabled_for_groups,
        updated_by=data.updated_by,
    )
    await storage.upsert_tenant_override(override)
    return {"status": "upserted", "key": key, "tenant_id": tenant_id}


async def delete_tenant_override(
    key: str,
    tenant_id: str,
    storage: AsyncSQLAlchemyStorage,
) -> dict:
    """Delete a tenant override."""
    await storage.delete_tenant_override(key, tenant_id)
    return {"status": "deleted", "key": key, "tenant_id": tenant_id}


@router.delete("/admin/{key}/tenants/{tenant_id}/")
async def admin_delete_override(
    key: str,
    tenant_id: str,
    storage: AsyncSQLAlchemyStorage = Depends(get_storage),
):
    """Delete a tenant override (admin only)."""
    return await delete_tenant_override(key, tenant_id, storage)
