"""Django admin configuration for FlagForge."""

from django.contrib import admin

from .models import FeatureFlagDefinition, TenantFeatureFlag, TenantFlagOverride


@admin.register(FeatureFlagDefinition)
class PublicFlagAdmin(admin.ModelAdmin):
    """Admin for global feature flag definitions (shared/public schema)."""

    list_display = [
        "key",
        "name",
        "default_enabled",
        "is_public",
        "rollout_percentage",
        "deprecated",
    ]
    list_filter = ["default_enabled", "is_public", "deprecated"]
    search_fields = ["key", "name"]
    ordering = ["key"]


@admin.register(TenantFeatureFlag)
class TenantFlagAdmin(admin.ModelAdmin):
    """Admin for tenant flag overrides — column / schema mode."""

    list_display = ["key", "tenant_id", "enabled", "rollout_percentage"]
    list_filter = ["tenant_id"]
    search_fields = ["key__key", "tenant_id"]
    ordering = ["tenant_id", "key"]


@admin.register(TenantFlagOverride)
class TenantFlagOverrideAdmin(admin.ModelAdmin):
    """Admin for tenant flag overrides — hybrid mode (lives in tenant schema)."""

    list_display = ["key", "enabled", "rollout_percentage", "updated_at", "updated_by"]
    search_fields = ["key__key"]
    ordering = ["key"]
