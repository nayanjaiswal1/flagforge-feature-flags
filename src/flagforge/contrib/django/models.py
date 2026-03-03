"""Django ORM models for FlagForge."""

from django.db import models


class FeatureFlagDefinition(models.Model):
    """Global feature flag definition.

    This model stores the base flag configuration that applies
    across all tenants unless overridden.
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
    """Tenant-specific override for a feature flag.

    This model stores tenant-specific overrides that modify the
    base flag behavior for a specific tenant.
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
