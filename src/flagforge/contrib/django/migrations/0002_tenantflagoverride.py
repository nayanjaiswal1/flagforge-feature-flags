"""Migration: add TenantFlagOverride model for hybrid tenancy mode."""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("django", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="TenantFlagOverride",
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
                    "enabled",
                    models.BooleanField(
                        blank=True,
                        null=True,
                        help_text="Override enabled state (None = use definition default)",
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
                        db_constraint=False,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="hybrid_overrides",
                        to="django.featureflagdefinition",
                    ),
                ),
            ],
            options={
                "db_table": "tenant_flag_override",
                "ordering": ["key"],
                "unique_together": {("key",)},
            },
        ),
    ]
