"""Django system checks for FlagForge."""

import importlib

from django.conf import settings
from django.core.checks import Error, Tags, register


@register(Tags.compatibility)
def check_tenancy_mode(app_configs, **kwargs):
    """Check that FLAGFORGE_TENANCY_MODE is valid."""
    errors = []
    mode = getattr(settings, "FLAGFORGE_TENANCY_MODE", "column")
    if mode not in ("column", "schema", "hybrid"):
        errors.append(
            Error(
                f"FLAGFORGE_TENANCY_MODE must be 'column', 'schema', or 'hybrid', got '{mode}'",
                id="flagforge.E001",
            )
        )
    return errors


@register(Tags.compatibility)
def check_cache_backend(app_configs, **kwargs):
    """Check that FLAGFORGE_CACHE_BACKEND is valid."""
    errors = []
    backend = getattr(settings, "FLAGFORGE_CACHE_BACKEND", "local")
    builtin = {"local", "redis", "none"}

    if backend not in builtin:
        # Must be a valid dotted import path
        if "." not in backend:
            errors.append(
                Error(
                    f"FLAGFORGE_CACHE_BACKEND '{backend}' is not a recognized value "
                    "('local', 'redis', 'none') and is not a dotted import path.",
                    id="flagforge.E002",
                )
            )
        else:
            try:
                module_path, class_name = backend.rsplit(".", 1)
                module = importlib.import_module(module_path)
                if not hasattr(module, class_name):
                    raise ImportError(f"No attribute '{class_name}' in '{module_path}'")
            except ImportError as e:
                errors.append(
                    Error(
                        f"FLAGFORGE_CACHE_BACKEND '{backend}' cannot be imported: {e}",
                        id="flagforge.E002",
                    )
                )

    if backend == "redis":
        has_redis_url = bool(getattr(settings, "FLAGFORGE_REDIS_URL", None))
        has_redis_host = bool(getattr(settings, "FLAGFORGE_REDIS_HOST", None))
        if not has_redis_url and not has_redis_host:
            errors.append(
                Error(
                    "FLAGFORGE_CACHE_BACKEND='redis' requires either FLAGFORGE_REDIS_URL "
                    "or FLAGFORGE_REDIS_HOST to be set.",
                    id="flagforge.E003",
                )
            )

    return errors


@register(Tags.compatibility)
def check_resolvers(app_configs, **kwargs):
    """Check that FLAGFORGE_TENANT_RESOLVER and FLAGFORGE_USER_RESOLVER are importable."""
    errors = []

    for setting_name, error_id in [
        ("FLAGFORGE_TENANT_RESOLVER", "flagforge.E004"),
        ("FLAGFORGE_USER_RESOLVER", "flagforge.E005"),
    ]:
        dotted = getattr(settings, setting_name, None)
        if not dotted:
            continue
        if "." not in dotted:
            errors.append(
                Error(
                    f"{setting_name} must be a dotted path to a callable, got '{dotted}'",
                    id=error_id,
                )
            )
            continue
        try:
            module_path, attr = dotted.rsplit(".", 1)
            module = importlib.import_module(module_path)
            if not hasattr(module, attr):
                raise ImportError(f"No attribute '{attr}' in '{module_path}'")
        except ImportError as e:
            errors.append(
                Error(
                    f"{setting_name} '{dotted}' cannot be imported: {e}",
                    id=error_id,
                )
            )

    return errors


@register(Tags.compatibility)
def check_admin_permission(app_configs, **kwargs):
    """Check that FLAGFORGE_ADMIN_PERMISSION is importable."""
    errors = []
    dotted = getattr(
        settings, "FLAGFORGE_ADMIN_PERMISSION", "rest_framework.permissions.IsAdminUser"
    )

    if "." not in dotted:
        errors.append(
            Error(
                f"FLAGFORGE_ADMIN_PERMISSION must be a dotted path to a DRF permission class, "
                f"got '{dotted}'",
                id="flagforge.E006",
            )
        )
        return errors

    try:
        module_path, class_name = dotted.rsplit(".", 1)
        module = importlib.import_module(module_path)
        if not hasattr(module, class_name):
            raise ImportError(f"No attribute '{class_name}' in '{module_path}'")
    except ImportError as e:
        errors.append(
            Error(
                f"FLAGFORGE_ADMIN_PERMISSION '{dotted}' cannot be imported: {e}",
                id="flagforge.E006",
            )
        )

    return errors


@register(Tags.compatibility)
def check_cache_ttl(app_configs, **kwargs):
    """Check that FLAGFORGE_CACHE_TTL is a positive integer."""
    errors = []
    ttl = getattr(settings, "FLAGFORGE_CACHE_TTL", 300)
    if not isinstance(ttl, int) or ttl <= 0:
        errors.append(
            Error(
                f"FLAGFORGE_CACHE_TTL must be a positive integer, got {ttl!r}",
                id="flagforge.E007",
            )
        )
    return errors
