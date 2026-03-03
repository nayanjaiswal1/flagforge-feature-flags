"""Cache key builders for FlagForge.

Provides smart cache key generation based on the TenantOverride.
If override has user/group targeting, uses user-specific keys.
Otherwise, uses resolved keys to avoid per-user cache explosion.
"""

from flagforge.core.models import TenantOverride


class CacheKeys:
    """Cache key builder with smart key selection.

    Key formats:
    - Resolved (no user/group targeting): ff:resolved:{tenant_id}:{flag_key}
    - User-targeted (has user/group lists): ff:user:{tenant_id}:{user_id}:{flag_key}
    - Definition: ff:def:{flag_key}

    TTLs (in seconds):
    - Resolved: 300
    - User-targeted: 300
    - Definition: 3600
    """

    PREFIX = "ff:"
    RESOLVED_PREFIX = "ff:resolved:"
    USER_PREFIX = "ff:user:"
    DEFINITION_PREFIX = "ff:def:"

    TTL_RESOLVED = 300
    TTL_USER = 300
    TTL_DEFINITION = 3600

    @staticmethod
    def has_targeting(override: TenantOverride | None) -> bool:
        """Check if override has user or group targeting.

        Args:
            override: The TenantOverride to check (can be None)

        Returns:
            True if override has enabled_for_users or enabled_for_groups
        """
        if override is None:
            return False
        return len(override.enabled_for_users) > 0 or len(override.enabled_for_groups) > 0

    @classmethod
    def resolved_key(cls, tenant_id: str | None, flag_key: str) -> str:
        """Generate cache key for resolved flag value (no user targeting).

        Use this when override has no user/group lists.

        Args:
            tenant_id: Tenant identifier (can be None for global flags)
            flag_key: Feature flag key

        Returns:
            Cache key in format: ff:resolved:{tenant_id}:{flag_key}
        """
        if tenant_id:
            return f"{cls.RESOLVED_PREFIX}{tenant_id}:{flag_key}"
        return f"{cls.RESOLVED_PREFIX}{flag_key}"

    @classmethod
    def user_key(cls, tenant_id: str | None, user_id: str, flag_key: str) -> str:
        """Generate cache key for user-specific flag value.

        Use this when override has user/group lists.

        Args:
            tenant_id: Tenant identifier (can be None for global flags)
            user_id: User identifier
            flag_key: Feature flag key

        Returns:
            Cache key in format: ff:user:{tenant_id}:{user_id}:{flag_key}
        """
        if tenant_id:
            return f"{cls.USER_PREFIX}{tenant_id}:{user_id}:{flag_key}"
        return f"{cls.USER_PREFIX}{user_id}:{flag_key}"

    @classmethod
    def definition_key(cls, flag_key: str) -> str:
        """Generate cache key for flag definition.

        Args:
            flag_key: Feature flag key

        Returns:
            Cache key in format: ff:def:{flag_key}
        """
        return f"{cls.DEFINITION_PREFIX}{flag_key}"

    @classmethod
    def select_key(
        cls,
        tenant_id: str | None,
        user_id: str | None,
        flag_key: str,
        override: TenantOverride | None,
    ) -> tuple[str, int]:
        """Select the appropriate cache key based on override.

        Smart selection:
        - If override has user/group targeting → use user_key (includes user_id)
        - Otherwise → use resolved_key (tenant-scoped, not user-scoped)

        Args:
            tenant_id: Tenant identifier
            user_id: User identifier (can be None for anonymous)
            flag_key: Feature flag key
            override: TenantOverride to inspect (can be None)

        Returns:
            Tuple of (cache_key, ttl_seconds)
        """
        if cls.has_targeting(override) and user_id:
            return cls.user_key(tenant_id, user_id, flag_key), cls.TTL_USER
        return cls.resolved_key(tenant_id, flag_key), cls.TTL_RESOLVED

    @classmethod
    def select_key_for_context(
        cls,
        tenant_id: str | None,
        user_id: str | None,
        flag_key: str,
        override: TenantOverride | None,
    ) -> str:
        """Select key without TTL (for get operations).

        Args:
            tenant_id: Tenant identifier
            user_id: User identifier
            flag_key: Feature flag key
            override: TenantOverride to inspect

        Returns:
            Cache key string
        """
        if cls.has_targeting(override) and user_id:
            return cls.user_key(tenant_id, user_id, flag_key)
        return cls.resolved_key(tenant_id, flag_key)
