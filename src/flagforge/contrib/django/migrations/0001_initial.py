"""Initial migration for FlagForge Django models."""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="FeatureFlagDefinition",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("key", models.CharField(db_index=True, max_length=255, unique=True)),
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, default="")),
                ("default_enabled", models.BooleanField(default=False)),
                ("is_public", models.BooleanField(default=False)),
                ("rollout_percentage", models.PositiveIntegerField(default=0)),
                ("deprecated", models.BooleanField(default=False)),
                (
                    "environments",
                    models.JSONField(
                        blank=True,
                        null=True,
                        help_text="List of allowed environments, e.g. ['staging', 'production']",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "feature_flag_definition",
                "ordering": ["key"],
            },
        ),
        migrations.CreateModel(
            name="TenantFeatureFlag",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "tenant_id",
                    models.CharField(db_index=True, max_length=255),
                ),
                (
                    "enabled",
                    models.BooleanField(
                        blank=True,
                        null=True,
                        help_text="Override enabled state (None = use default)",
                    ),
                ),
                (
                    "rollout_percentage",
                    models.PositiveIntegerField(
                        blank=True,
                        null=True,
                        help_text="Override rollout percentage (None = use definition default)",
                    ),
                ),
                (
                    "enabled_for_users",
                    models.JSONField(
                        default=list,
                        help_text="List of user IDs explicitly enabled for this flag",
                    ),
                ),
                (
                    "enabled_for_groups",
                    models.JSONField(
                        default=list,
                        help_text="List of group IDs enabled for this flag",
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "updated_by",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        null=True,
                        help_text="User who last updated this override",
                    ),
                ),
                (
                    "key",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tenant_overrides",
                        to="django.featureflagdefinition",
                    ),
                ),
            ],
            options={
                "db_table": "tenant_feature_flag",
                "unique_together": {("key", "tenant_id")},
                "ordering": ["tenant_id", "key"],
            },
        ),
    ]
