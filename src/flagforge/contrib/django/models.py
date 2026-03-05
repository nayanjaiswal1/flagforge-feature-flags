"""Django ORM models for FlagForge."""

from django.db import models


class FeatureFlagDefinition(models.Model):
    """Global feature flag definition.

    This model stores the base flag configuration that applies
    across all tenants unless overridden.

    In hybrid mode this lives in the public/shared schema (SHARED_APPS).
    In column mode it lives in the same schema as TenantFeatureFlag.
    """

    key = models.CharField(max_length=255, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    default_enabled = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    rollout_percentage = models.PositiveIntegerField(default=0)
    deprecated = models.BooleanField(default=False)
    environments = models.JSONField(
        null=True,
        blank=True,
        help_text="List of allowed environments, e.g. ['staging', 'production']",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "feature_flag_definition"
        ordering = ["key"]

    def __str__(self):
        return f"{self.name} ({self.key})"


class TenantFeatureFlag(models.Model):
    """Tenant-specific override for a feature flag — column / schema modes.

    Used when FLAGFORGE_TENANCY_MODE is 'column' or 'schema'.
    The tenant_id column discriminates between tenants (column mode),
    or the model lives in a per-tenant schema (schema mode).
    """

    key = models.ForeignKey(
        FeatureFlagDefinition,
        on_delete=models.CASCADE,
        related_name="tenant_overrides",
    )
    tenant_id = models.CharField(max_length=255, db_index=True)
    enabled = models.BooleanField(
        null=True,
        blank=True,
        help_text="Override enabled state (None = use default)",
    )
    rollout_percentage = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Override rollout percentage (None = use definition default)",
    )
    enabled_for_users = models.JSONField(
        default=list,
        help_text="List of user IDs explicitly enabled for this flag",
    )
    enabled_for_groups = models.JSONField(
        default=list,
        help_text="List of group IDs enabled for this flag",
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="User who last updated this override",
    )

    class Meta:
        db_table = "tenant_feature_flag"
        unique_together = ["key", "tenant_id"]
        ordering = ["tenant_id", "key"]

    def __str__(self):
        return f"{self.key.key} for {self.tenant_id}"


class TenantFlagOverride(models.Model):
    """Tenant-specific override for a feature flag — hybrid mode.

    Used when FLAGFORGE_TENANCY_MODE is 'hybrid'.

    In hybrid mode this model lives in each tenant's private schema
    (django-tenants TENANT_APPS). There is no tenant_id column — schema
    routing provides the isolation. FeatureFlagDefinition (the definition)
    stays in the shared/public schema, giving you a single control plane.

    This is the "Hybrid Gold Standard":
      - Definitions   → public schema  (one place to manage all flags)
      - Overrides     → tenant schema  (strict per-tenant data residency)
    """

    key = models.ForeignKey(
        FeatureFlagDefinition,
        on_delete=models.CASCADE,
        related_name="hybrid_overrides",
        db_constraint=False,  # FK crosses schema boundary in django-tenants
    )
    enabled = models.BooleanField(
        null=True,
        blank=True,
        help_text="Override enabled state (None = use definition default)",
    )
    rollout_percentage = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Override rollout percentage (None = use definition default)",
    )
    enabled_for_users = models.JSONField(
        default=list,
        help_text="List of user IDs explicitly enabled for this flag",
    )
    enabled_for_groups = models.JSONField(
        default=list,
        help_text="List of group IDs enabled for this flag",
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="User who last updated this override",
    )

    class Meta:
        db_table = "tenant_flag_override"
        # Unique per flag within the tenant's schema (no tenant_id needed)
        unique_together = [["key"]]
        ordering = ["key"]

    def __str__(self):
        return f"override for {self.key.key}"
