"""Django system checks for FlagForge."""

from django.conf import settings
from django.core.checks import Error, Tags, register


@register(Tags.compatibility)
def check_tenancy_mode(app_configs, **kwargs):
    """Check that FLAGFORGE_TENANCY_MODE is valid."""
    errors = []
    mode = getattr(settings, "FLAGFORGE_TENANCY_MODE", "column")

    if mode not in ("column", "schema"):
        errors.append(
            Error(
                f"FLAGFORGE_TENANCY_MODE must be 'column' or 'schema', got '{mode}'",
                id="flagforge.E001",
            )
        )

    return errors
