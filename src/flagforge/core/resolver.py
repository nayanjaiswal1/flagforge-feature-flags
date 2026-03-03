"""Feature flag resolution logic."""

from flagforge.core.context import FeatureContext
from flagforge.core.hasher import evaluate_rollout
from flagforge.core.models import FlagDefinition, TenantOverride


def resolve(
    definition: FlagDefinition,
    override: TenantOverride | None,
    context: FeatureContext,
) -> bool:
    """Resolve a feature flag based on definition, override, and context.

    Priority chain:
      Step 0 (ENV): If definition.environments set and context.environment not in list -> False
      Step 1 (USER): If override and context.user_id in override.enabled_for_users -> True
      Step 2 (GROUP): If override and any group in context.group_ids intersects enabled_for_groups -> True
      Step 3 (OVERRIDE): If override.enabled is not None -> use override
      Step 4 (DEFAULT): Use definition.default_enabled

    Rollout applies ONLY when default_enabled=True and rollout_percentage > 0.

    Args:
        definition: Flag definition with default settings
        override: Tenant-specific override (None = no override)
        context: Feature context for evaluation

    Returns:
        bool: Whether the flag is enabled for this context
    """
    # Step 0: Environment gate
    if definition.environments is not None and context.environment not in definition.environments:
        return False

    # Pre-compute tenant once
    tenant = context.tenant_id if context.tenant_id is not None else ""

    # If no override, use definition default
    if override is None:
        # Step 4: Use default_enabled as base
        if definition.default_enabled:
            # Apply gradual rollout only if rollout_percentage > 0
            if definition.rollout_percentage > 0:
                return evaluate_rollout(
                    tenant,
                    definition.key,
                    context.user_id,
                    definition.rollout_percentage,
                )
            return True
        return False

    # Step 1: User targeting - use set for O(1) lookup
    enabled_users = override.enabled_for_users
    if context.user_id is not None and enabled_users and context.user_id in enabled_users:
        return True

    # Step 2: Group targeting - use set intersection for O(min(n,m))
    enabled_groups = override.enabled_for_groups
    if enabled_groups and context.group_ids and set(context.group_ids) & set(enabled_groups):
        return True

    # Step 3: Override enabled/disabled
    if override.enabled is not None:
        if override.enabled:
            # Apply gradual rollout if override has rollout_percentage > 0
            rollout_pct = override.rollout_percentage
            if rollout_pct is not None and rollout_pct > 0:
                return evaluate_rollout(
                    tenant,
                    definition.key,
                    context.user_id,
                    rollout_pct,
                )
            return True
        return False

    # Fall back to definition default
    if definition.default_enabled:
        if definition.rollout_percentage > 0:
            return evaluate_rollout(
                tenant,
                definition.key,
                context.user_id,
                definition.rollout_percentage,
            )
        return True
    return False
