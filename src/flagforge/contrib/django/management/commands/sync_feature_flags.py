"""Management command to sync feature flags from YAML."""

from django.core.management.base import BaseCommand

from flagforge.storage.yaml_loader import load_flags


class Command(BaseCommand):
    """Sync feature flags from feature-flags.yaml config file."""

    help = "Sync feature flags from feature-flags.yaml"

    def add_arguments(self, parser):
        parser.add_argument(
            "--config",
            type=str,
            default="config/feature-flags.yaml",
            help="Path to feature-flags.yaml",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without making changes",
        )
        parser.add_argument(
            "--remove-deprecated",
            action="store_true",
            help="Remove flags marked as deprecated",
        )

    def handle(self, *args, **options):
        config_path = options["config"]
        dry_run = options["dry_run"]
        remove_deprecated = options["remove_deprecated"]

        try:
            flags = load_flags(config_path)
        except Exception as e:
            self.stderr.write(f"Error loading {config_path}: {e}")
            return

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No changes will be made"))
            for flag in flags:
                self.stdout.write(f"  Would sync: {flag.key} ({flag.name})")
            return

        from flagforge.contrib.django.models import FeatureFlagDefinition

        for flag in flags:
            FeatureFlagDefinition.objects.update_or_create(
                key=flag.key,
                defaults={
                    "name": flag.name,
                    "description": flag.description,
                    "default_enabled": flag.default_enabled,
                    "is_public": flag.is_public,
                    "rollout_percentage": flag.rollout_percentage,
                    "deprecated": flag.deprecated,
                    "environments": flag.environments,
                },
            )
            self.stdout.write(f"Synced: {flag.key}")

        if remove_deprecated:
            deprecated = FeatureFlagDefinition.objects.filter(deprecated=True)
            count = deprecated.count()
            if count > 0:
                deprecated.delete()
                self.stdout.write(f"Removed {count} deprecated flags")
