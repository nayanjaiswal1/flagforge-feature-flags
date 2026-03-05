"""Django storage backend for FlagForge."""

from django.conf import settings

from flagforge.core.exceptions import StorageError
from flagforge.core.models import FlagDefinition, TenantOverride
from flagforge.storage.base import StorageBackend

from .models import FeatureFlagDefinition, TenantFeatureFlag, TenantFlagOverride

_VALID_MODES = ("column", "schema", "hybrid")


class DjangoStorage(StorageBackend):
    """Django ORM-based storage backend for feature flags.

    Supports three multi-tenancy modes via FLAGFORGE_TENANCY_MODE:

    - 'column'  (default): Both models in the same schema. tenant_id column
                           discriminates between tenants. Works with any Django
                           setup, no extra routing needed.

    - 'schema':            TenantFeatureFlag lives in a per-tenant schema managed
                           by django-tenants. tenant_id column is still present
                           for compatibility but the schema provides isolation.

    - 'hybrid':            Hybrid Gold Standard.
                           FeatureFlagDefinition  → public/shared schema (control plane)
                           TenantFlagOverride     → each tenant's private schema
                           No tenant_id column on overrides — schema routing is the
                           sole source of isolation. Strict data residency.
    """

    def __init__(self, tenancy_mode: str | None = None):
        self.tenancy_mode = tenancy_mode or getattr(settings, "FLAGFORGE_TENANCY_MODE", "column")
        if self.tenancy_mode not in _VALID_MODES:
            raise StorageError(
                f"Invalid FLAGFORGE_TENANCY_MODE: {self.tenancy_mode!r}. "
                f"Must be one of {_VALID_MODES}."
            )

    # ------------------------------------------------------------------
    # Definitions  (always go through FeatureFlagDefinition)
    # ------------------------------------------------------------------

    def get_definition(self, key: str) -> FlagDefinition | None:
        try:
            obj = FeatureFlagDefinition.objects.get(key=key)
            return self._to_flag_definition(obj)
        except FeatureFlagDefinition.DoesNotExist:
            return None

    def get_all_definitions(self) -> list[FlagDefinition]:
        return [self._to_flag_definition(obj) for obj in FeatureFlagDefinition.objects.all()]

    def upsert_definition(self, defn: FlagDefinition) -> None:
        FeatureFlagDefinition.objects.update_or_create(
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

    def delete_definition(self, key: str) -> None:
        FeatureFlagDefinition.objects.filter(key=key).delete()

    # ------------------------------------------------------------------
    # Overrides  (routed by tenancy_mode)
    # ------------------------------------------------------------------

    def get_tenant_override(self, key: str, tenant_id: str) -> TenantOverride | None:
        if self.tenancy_mode == "hybrid":
            return self._hybrid_get_override(key, tenant_id)
        return self._column_get_override(key, tenant_id)

    def get_all_tenant_overrides(self, tenant_id: str) -> list[TenantOverride]:
        if self.tenancy_mode == "hybrid":
            return self._hybrid_get_all_overrides(tenant_id)
        return self._column_get_all_overrides(tenant_id)

    def upsert_tenant_override(self, override: TenantOverride) -> None:
        if self.tenancy_mode == "hybrid":
            self._hybrid_upsert_override(override)
        else:
            self._column_upsert_override(override)

    def delete_tenant_override(self, key: str, tenant_id: str) -> None:
        if self.tenancy_mode == "hybrid":
            self._hybrid_delete_override(key)
        else:
            TenantFeatureFlag.objects.filter(key__key=key, tenant_id=tenant_id).delete()

    # ------------------------------------------------------------------
    # Column / schema mode helpers  (TenantFeatureFlag)
    # ------------------------------------------------------------------

    def _column_get_override(self, key: str, tenant_id: str) -> TenantOverride | None:
        try:
            obj = TenantFeatureFlag.objects.get(key__key=key, tenant_id=tenant_id)
            return self._to_tenant_override_from_column(obj)
        except TenantFeatureFlag.DoesNotExist:
            return None

    def _column_get_all_overrides(self, tenant_id: str) -> list[TenantOverride]:
        qs = TenantFeatureFlag.objects.filter(tenant_id=tenant_id).select_related("key")
        return [self._to_tenant_override_from_column(obj) for obj in qs]

    def _column_upsert_override(self, override: TenantOverride) -> None:
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

    # ------------------------------------------------------------------
    # Hybrid mode helpers  (TenantFlagOverride — no tenant_id)
    # ------------------------------------------------------------------

    def _hybrid_get_override(self, key: str, tenant_id: str) -> TenantOverride | None:
        """In hybrid mode, the active schema IS the tenant — tenant_id unused for lookup."""
        try:
            obj = TenantFlagOverride.objects.select_related("key").get(key__key=key)
            return self._to_tenant_override_from_hybrid(obj, tenant_id)
        except TenantFlagOverride.DoesNotExist:
            return None

    def _hybrid_get_all_overrides(self, tenant_id: str) -> list[TenantOverride]:
        qs = TenantFlagOverride.objects.select_related("key").all()
        return [self._to_tenant_override_from_hybrid(obj, tenant_id) for obj in qs]

    def _hybrid_upsert_override(self, override: TenantOverride) -> None:
        flag = FeatureFlagDefinition.objects.get(key=override.key)
        TenantFlagOverride.objects.update_or_create(
            key=flag,
            defaults={
                "enabled": override.enabled,
                "rollout_percentage": override.rollout_percentage,
                "enabled_for_users": override.enabled_for_users,
                "enabled_for_groups": override.enabled_for_groups,
                "updated_by": override.updated_by,
            },
        )

    def _hybrid_delete_override(self, key: str) -> None:
        TenantFlagOverride.objects.filter(key__key=key).delete()

    # ------------------------------------------------------------------
    # Converters
    # ------------------------------------------------------------------

    def _to_flag_definition(self, obj: FeatureFlagDefinition) -> FlagDefinition:
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

    def _to_tenant_override_from_column(self, obj: TenantFeatureFlag) -> TenantOverride:
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

    def _to_tenant_override_from_hybrid(
        self, obj: TenantFlagOverride, tenant_id: str
    ) -> TenantOverride:
        return TenantOverride(
            key=obj.key.key,
            tenant_id=tenant_id,  # injected from context — not stored in the row
            enabled=obj.enabled,
            rollout_percentage=obj.rollout_percentage,
            enabled_for_users=obj.enabled_for_users or [],
            enabled_for_groups=obj.enabled_for_groups or [],
            updated_at=obj.updated_at,
            updated_by=obj.updated_by,
        )


class DjangoStorageAdapter:
    """Adapter for Django storage to FlagEngine interface."""

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
