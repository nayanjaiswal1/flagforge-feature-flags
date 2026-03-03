"""Django storage backend for FlagForge."""

from django.conf import settings

from flagforge.core.exceptions import StorageError
from flagforge.core.models import FlagDefinition, TenantOverride
from flagforge.storage.base import StorageBackend

from .models import FeatureFlagDefinition, TenantFeatureFlag


class DjangoStorage(StorageBackend):
    """Django ORM-based storage backend for feature flags.

    Supports both column-based and schema-based multi-tenancy.
    Configure via FLAGFORGE_TENANCY_MODE setting.
    """

    def __init__(self, tenancy_mode: str | None = None):
        """Initialize Django storage.

        Args:
            tenancy_mode: Either 'column' (default) or 'schema'
        """
        self.tenancy_mode = tenancy_mode or getattr(settings, "FLAGFORGE_TENANCY_MODE", "column")
        if self.tenancy_mode not in ("column", "schema"):
            raise StorageError(
                f"Invalid FLAGFORGE_TENANCY_MODE: {self.tenancy_mode}. "
                "Must be 'column' or 'schema'."
            )

    def _get_queryset(self, tenant_id: str):
        """Get filtered queryset based on tenancy mode."""
        if self.tenancy_mode in {"column", "schema"}:
            return TenantFeatureFlag.objects.filter(tenant_id=tenant_id)
        raise StorageError(f"Unknown tenancy mode: {self.tenancy_mode}")

    def get_definition(self, key: str) -> FlagDefinition | None:
        """Get a flag definition by key."""
        try:
            obj = FeatureFlagDefinition.objects.get(key=key)
            return self._to_flag_definition(obj)
        except FeatureFlagDefinition.DoesNotExist:
            return None

    def get_all_definitions(self) -> list[FlagDefinition]:
        """Get all flag definitions."""
        return [self._to_flag_definition(obj) for obj in FeatureFlagDefinition.objects.all()]

    def get_tenant_override(self, key: str, tenant_id: str) -> TenantOverride | None:
        """Get tenant-specific override for a flag."""
        try:
            obj = TenantFeatureFlag.objects.get(key__key=key, tenant_id=tenant_id)
            return self._to_tenant_override(obj)
        except TenantFeatureFlag.DoesNotExist:
            return None

    def get_all_tenant_overrides(self, tenant_id: str) -> list[TenantOverride]:
        """Get all overrides for a tenant."""
        return [
            self._to_tenant_override(obj)
            for obj in self._get_queryset(tenant_id).select_related("key")
        ]

    def upsert_definition(self, defn: FlagDefinition) -> None:
        """Create or update a flag definition."""
        _obj, _ = FeatureFlagDefinition.objects.update_or_create(
            key=defn.key,
            defaults={
                "name": defn.name,
                "description": defn.description,
                "default_enabled": defn.default_enabled,
                "is_public": defn.is_public,
                "rollout_percentage": defn.rollout_percentage,
                "deprecated": defn.deprecated,
                "environments": defn.environments,
            },
        )

    def upsert_tenant_override(self, override: TenantOverride) -> None:
        """Create or update a tenant override."""
        flag = FeatureFlagDefinition.objects.get(key=override.key)
        TenantFeatureFlag.objects.update_or_create(
            key=flag,
            tenant_id=override.tenant_id,
            defaults={
                "enabled": override.enabled,
                "rollout_percentage": override.rollout_percentage,
                "enabled_for_users": override.enabled_for_users,
                "enabled_for_groups": override.enabled_for_groups,
                "updated_by": override.updated_by,
            },
        )

    def delete_tenant_override(self, key: str, tenant_id: str) -> None:
        """Delete a tenant override."""
        TenantFeatureFlag.objects.filter(key__key=key, tenant_id=tenant_id).delete()

    def delete_definition(self, key: str) -> None:
        """Delete a flag definition and all its tenant overrides."""
        FeatureFlagDefinition.objects.filter(key=key).delete()

    def _to_flag_definition(self, obj: FeatureFlagDefinition) -> FlagDefinition:
        """Convert ORM model to FlagDefinition."""
        return FlagDefinition(
            key=obj.key,
            name=obj.name,
            description=obj.description,
            default_enabled=obj.default_enabled,
            is_public=obj.is_public,
            rollout_percentage=obj.rollout_percentage,
            deprecated=obj.deprecated,
            environments=obj.environments,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )

    def _to_tenant_override(self, obj: TenantFeatureFlag) -> TenantOverride:
        """Convert ORM model to TenantOverride."""
        return TenantOverride(
            key=obj.key.key,
            tenant_id=obj.tenant_id,
            enabled=obj.enabled,
            rollout_percentage=obj.rollout_percentage,
            enabled_for_users=obj.enabled_for_users or [],
            enabled_for_groups=obj.enabled_for_groups or [],
            updated_at=obj.updated_at,
            updated_by=obj.updated_by,
        )


class DjangoStorageAdapter:
    """Adapter for Django storage to FlagEngine interface.

    This provides the interface expected by FlagEngine.
    """

    def __init__(self, tenancy_mode: str | None = None):
        self._storage = DjangoStorage(tenancy_mode)

    def get_definition(self, key: str) -> FlagDefinition | None:
        return self._storage.get_definition(key)

    def get_tenant_override(self, key: str, tenant_id: str) -> TenantOverride | None:
        return self._storage.get_tenant_override(key, tenant_id)

    def get_all_definitions(self) -> list[FlagDefinition]:
        return self._storage.get_all_definitions()

    def get_all_tenant_overrides(self, tenant_id: str) -> list[TenantOverride]:
        return self._storage.get_all_tenant_overrides(tenant_id)

    def upsert_definition(self, defn: FlagDefinition) -> None:
        return self._storage.upsert_definition(defn)

    def upsert_tenant_override(self, override: TenantOverride) -> None:
        return self._storage.upsert_tenant_override(override)

    def delete_tenant_override(self, key: str, tenant_id: str) -> None:
        return self._storage.delete_tenant_override(key, tenant_id)

    def delete_definition(self, key: str) -> None:
        return self._storage.delete_definition(key)
