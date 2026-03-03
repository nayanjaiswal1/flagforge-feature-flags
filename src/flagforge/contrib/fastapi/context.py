"""FastAPI context factory for FlagForge."""

from fastapi import Request

from flagforge.core.context import FeatureContext


def context_factory(request: Request) -> FeatureContext:
    """Create a FeatureContext from a FastAPI request.

    This factory extracts tenant_id, user_id, group_ids, and environment
    from the incoming request to build a FeatureContext for flag evaluation.

    Args:
        request: FastAPI Request object

    Returns:
        FeatureContext populated from the request
    """
    tenant_id: str | None = None
    user_id: str | None = None
    group_ids: list[str] = []
    environment: str | None = None

    # Try to get tenant from headers or state
    tenant_id = request.headers.get("X-Tenant-ID")
    if not tenant_id and hasattr(request, "state") and hasattr(request.state, "tenant_id"):
        tenant_id = request.state.tenant_id

    # Try to get user from headers, auth, or state
    user_id = request.headers.get("X-User-ID")

    # Safely check for auth/user (Starlette raises if middleware not installed)
    scope = request.scope

    if not user_id and "auth" in scope and request.auth is not None:
        if hasattr(request.auth, "sub"):
            user_id = request.auth.sub
        elif hasattr(request.auth, "user_id"):
            user_id = request.auth.user_id

    if not user_id and "user" in scope and request.user is not None:
        if hasattr(request.user, "id") and request.user.id:
            user_id = str(request.user.id)
        if hasattr(request.user, "groups"):
            group_ids = [g.name for g in request.user.groups.all()]

    if hasattr(request, "state") and hasattr(request.state, "environment"):
        environment = request.state.environment

    custom_attrs = {}
    if hasattr(request, "state") and hasattr(request.state, "flagforge_attrs"):
        custom_attrs = request.state.flagforge_attrs

    return FeatureContext(
        tenant_id=tenant_id,
        user_id=user_id,
        group_ids=group_ids,
        environment=environment,
        attributes=custom_attrs,
    )
