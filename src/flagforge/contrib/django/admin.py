"""Django admin configuration for FlagForge."""

from django.contrib import admin

from .models import FeatureFlagDefinition, TenantFeatureFlag


@admin.register(FeatureFlagDefinition)
class PublicFlagAdmin(admin.ModelAdmin):
    """Admin for global feature flag definitions."""

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
    """Admin for tenant-specific flag overrides."""

    list_display = ["key", "tenant_id", "enabled", "rollout_percentage"]
    list_filter = ["tenant_id"]
    search_fields = ["key__key", "tenant_id"]
    ordering = ["tenant_id", "key"]
