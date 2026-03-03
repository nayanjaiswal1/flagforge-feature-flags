"""Management command to show feature flag status."""

from django.core.management.base import BaseCommand

from flagforge.cache import LocalCache
from flagforge.contrib.django.storage import DjangoStorageAdapter
from flagforge.core.context import FeatureContext
from flagforge.core.engine import FlagEngine


class Command(BaseCommand):
    """Show feature flag status for a tenant."""

    help = "Show feature flag status for a tenant"

    def add_arguments(self, parser):
        parser.add_argument(
            "--tenant",
            type=str,
            required=True,
            help="Tenant ID",
        )
        parser.add_argument(
            "--flag",
            type=str,
            help="Specific flag key to check",
        )

    def handle(self, *args, **options):
        tenant_id = options["tenant"]
        flag_key = options.get("flag")

        storage = DjangoStorageAdapter()
        cache = LocalCache()
        engine = FlagEngine(storage=storage, cache=cache)

        context = FeatureContext(tenant_id=tenant_id)

        if flag_key:
            is_enabled = engine.is_enabled(flag_key, context)
            status = "ENABLED" if is_enabled else "DISABLED"
            self.stdout.write(f"{flag_key}: {status}")
        else:
            results = engine.evaluate_all(context)
            for key, enabled in results.items():
                status = "ENABLED" if enabled else "DISABLED"
                self.stdout.write(f"{key}: {status}")
