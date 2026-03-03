"""Django engine singleton and utilities for FlagForge."""

from django.conf import settings
from django.http import HttpRequest

from flagforge.cache import LocalCache
from flagforge.contrib.django.storage import DjangoStorageAdapter
from flagforge.core.context import FeatureContext
from flagforge.core.engine import FlagEngine

_engine = None


def get_engine() -> FlagEngine:
    """Get or create a singleton FlagEngine instance for Django."""
    global _engine
    if _engine is None:
        storage = DjangoStorageAdapter()
        cache = LocalCache()
        _engine = FlagEngine(storage=storage, cache=cache)
    return _engine


def flag_enabled(key: str, request: HttpRequest | None = None) -> bool:
    """Simple function to check if a feature flag is enabled.

    This function automatically handles the context and engine logic,
    making it as simple as a single model check.

    Args:
        key: The feature flag key to check
        request: Optional Django request object to automatically pull context

    Returns:
        bool: Whether the flag is enabled
    """
    engine = get_engine()

    # Build context from request if provided
    tenant_id = None
    user_id = None
    group_ids = []
    environment = getattr(settings, "FLAGFORGE_ENVIRONMENT", "production")

    if request:
        # Try to get tenant_id from common patterns (request.tenant, request.tenant_id, etc.)
        tenant_id = getattr(request, "tenant_id", None)
        if not tenant_id and hasattr(request, "tenant"):
            # Supports django-tenants and similar packages
            tenant_id = getattr(request.tenant, "schema_name", str(request.tenant))

        # Pull user info
        if hasattr(request, "user") and request.user.is_authenticated:
            user_id = str(request.user.id)
            if hasattr(request.user, "groups"):
                group_ids = [str(g.id) for g in request.user.groups.all()]

    # Fallback for non-tenant apps
    if not tenant_id:
        tenant_id = getattr(settings, "FLAGFORGE_DEFAULT_TENANT_ID", "default")

    context = FeatureContext(
        tenant_id=tenant_id,
        user_id=user_id,
        group_ids=group_ids,
        environment=environment,
    )

    return engine.is_enabled(key, context)
