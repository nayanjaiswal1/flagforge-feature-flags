"""FlagForge CLI - Command-line interface for managing feature flags."""

import os
import sys

import click


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """FlagForge - Enterprise Multi-Tenant Feature Flag Control Plane."""
    pass


@cli.command()
@click.option(
    "--config",
    type=click.Path(exists=True),
    default="config/feature-flags.yaml",
    help="Path to feature-flags.yaml",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without making changes",
)
@click.option(
    "--remove-deprecated",
    is_flag=True,
    help="Remove flags marked as deprecated",
)
@click.option(
    "--app",
    type=str,
    help="Dotted path to app with get_engine() factory (or use DJANGO_SETTINGS_MODULE)",
)
def sync(config: str, dry_run: bool, remove_deprecated: bool, app: str | None):
    """Sync feature flags from feature-flags.yaml config file."""
    from flagforge.storage.yaml_loader import load_flags

    try:
        flags = load_flags(config)
    except Exception as e:
        click.echo(f"Error loading {config}: {e}", err=True)
        sys.exit(1)

    if dry_run:
        click.echo(click.style("DRY RUN - No changes will be made", fg="yellow"))
        for flag in flags:
            click.echo(f"  Would sync: {flag.key} ({flag.name})")
        return

    django_settings = os.environ.get("DJANGO_SETTINGS_MODULE")
    if django_settings or app:
        _sync_django(flags, remove_deprecated)
    else:
        click.echo("Error: Either --app or DJANGO_SETTINGS_MODULE required", err=True)
        sys.exit(1)


def _sync_django(flags, remove_deprecated: bool):
    """Sync flags to Django database."""
    import django
    from django.conf import settings

    if not settings.configured:
        click.echo("Error: Django not configured", err=True)
        sys.exit(1)

    django.setup()

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
        click.echo(f"Synced: {flag.key}")

    if remove_deprecated:
        deprecated = FeatureFlagDefinition.objects.filter(deprecated=True)
        count = deprecated.count()
        if count > 0:
            deprecated.delete()
            click.echo(f"Removed {count} deprecated flags")


@cli.command()
@click.option(
    "--tenant",
    type=str,
    required=True,
    help="Tenant ID",
)
@click.option(
    "--flag",
    type=str,
    help="Specific flag key to check",
)
@click.option(
    "--app",
    type=str,
    help="Dotted path to app with get_engine() factory",
)
def status(tenant: str, flag: str | None, app: str | None):
    """Show feature flag status for a tenant."""
    engine = _get_engine(app)

    from flagforge.core.context import FeatureContext

    context = FeatureContext(tenant_id=tenant)

    if flag:
        is_enabled = engine.is_enabled(flag, context)
        status_text = "ENABLED" if is_enabled else "DISABLED"
        click.echo(f"{flag}: {status_text}")
    else:
        results = engine.evaluate_all(context)
        for key, enabled in results.items():
            status_text = "ENABLED" if enabled else "DISABLED"
            click.echo(f"{key}: {status_text}")


@cli.command()
@click.option(
    "--flag",
    type=str,
    required=True,
    help="Feature flag key",
)
@click.option(
    "--tenant",
    type=str,
    required=True,
    help="Tenant ID",
)
@click.option(
    "--app",
    type=str,
    help="Dotted path to app with get_engine() factory",
)
def enable(flag: str, tenant: str, app: str | None):
    """Enable a feature flag for a specific tenant."""
    django_settings = os.environ.get("DJANGO_SETTINGS_MODULE")
    if not django_settings and not app:
        click.echo("Error: Either --app or DJANGO_SETTINGS_MODULE required", err=True)
        sys.exit(1)

    import django
    from django.conf import settings

    if not settings.configured:
        django.setup()

    from flagforge.contrib.django.models import FeatureFlagDefinition, TenantFeatureFlag

    try:
        flag_obj = FeatureFlagDefinition.objects.get(key=flag)
    except FeatureFlagDefinition.DoesNotExist:
        click.echo(f"Flag '{flag}' not found", err=True)
        sys.exit(1)

    TenantFeatureFlag.objects.update_or_create(
        key=flag_obj,
        tenant_id=tenant,
        defaults={"enabled": True},
    )

    click.echo(f"Enabled '{flag}' for tenant '{tenant}'")


@cli.command()
@click.option(
    "--flag",
    type=str,
    required=True,
    help="Feature flag key",
)
@click.option(
    "--tenant",
    type=str,
    required=True,
    help="Tenant ID",
)
@click.option(
    "--app",
    type=str,
    help="Dotted path to app with get_engine() factory",
)
def disable(flag: str, tenant: str, app: str | None):
    """Disable a feature flag for a specific tenant."""
    django_settings = os.environ.get("DJANGO_SETTINGS_MODULE")
    if not django_settings and not app:
        click.echo("Error: Either --app or DJANGO_SETTINGS_MODULE required", err=True)
        sys.exit(1)

    import django
    from django.conf import settings

    if not settings.configured:
        django.setup()

    from flagforge.contrib.django.models import FeatureFlagDefinition, TenantFeatureFlag

    try:
        flag_obj = FeatureFlagDefinition.objects.get(key=flag)
    except FeatureFlagDefinition.DoesNotExist:
        click.echo(f"Flag '{flag}' not found", err=True)
        sys.exit(1)

    TenantFeatureFlag.objects.update_or_create(
        key=flag_obj,
        tenant_id=tenant,
        defaults={"enabled": False},
    )

    click.echo(f"Disabled '{flag}' for tenant '{tenant}'")


@cli.command()
@click.option(
    "--tenant",
    type=str,
    help="Specific tenant ID to clear (clears all if not specified)",
)
@click.option(
    "--flag",
    type=str,
    help="Specific flag key to clear",
)
@click.option(
    "--app",
    type=str,
    help="Dotted path to app with get_engine() factory",
)
def clear_cache(tenant: str | None, flag: str | None, app: str | None):
    """Clear feature flag cache."""
    _get_engine(app)

    from flagforge.cache import LocalCache

    cache = LocalCache()

    if flag:
        cache.delete_for_flag(flag)
        click.echo(f"Cleared cache for flag: {flag}")
    elif tenant:
        cache.delete_for_tenant(tenant)
        click.echo(f"Cleared cache for tenant: {tenant}")
    else:
        cache.clear_request_cache()
        click.echo("Cleared request cache")


def _get_engine(app: str | None):
    """Get the FlagEngine instance."""
    django_settings = os.environ.get("DJANGO_SETTINGS_MODULE")
    if not django_settings and not app:
        click.echo("Error: Either --app or DJANGO_SETTINGS_MODULE required", err=True)
        sys.exit(1)

    import django
    from django.conf import settings

    if not settings.configured:
        django.setup()

    from flagforge.cache import LocalCache
    from flagforge.contrib.django.storage import DjangoStorageAdapter
    from flagforge.core.engine import FlagEngine
    from flagforge.storage.base import StorageBackend

    storage: StorageBackend = DjangoStorageAdapter()  # type: ignore[assignment]
    cache = LocalCache()
    return FlagEngine(storage=storage, cache=cache)


if __name__ == "__main__":
    cli()
