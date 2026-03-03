"""Management command to enable a feature flag for a tenant."""

from django.core.management.base import BaseCommand

from flagforge.contrib.django.models import FeatureFlagDefinition, TenantFeatureFlag


class Command(BaseCommand):
    """Enable a feature flag for a specific tenant."""

    help = "Enable a feature flag for a tenant"

    def add_arguments(self, parser):
        parser.add_argument(
            "--flag",
            type=str,
            required=True,
            help="Feature flag key",
        )
        parser.add_argument(
            "--tenant",
            type=str,
            required=True,
            help="Tenant ID",
        )

    def handle(self, *args, **options):
        flag_key = options["flag"]
        tenant_id = options["tenant"]

        try:
            flag = FeatureFlagDefinition.objects.get(key=flag_key)
        except FeatureFlagDefinition.DoesNotExist:
            self.stderr.write(f"Flag '{flag_key}' not found")
            return

        _override, _ = TenantFeatureFlag.objects.update_or_create(
            key=flag,
            tenant_id=tenant_id,
            defaults={
                "enabled": True,
            },
        )

        self.stdout.write(f"Enabled '{flag_key}' for tenant '{tenant_id}'")
