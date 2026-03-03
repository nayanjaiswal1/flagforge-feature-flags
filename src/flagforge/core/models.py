"""FlagForge data models."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class FlagDefinition:
    """Represents a feature flag definition.

    Attributes:
        key: Unique identifier for the flag
        name: Human-readable name
        description: Optional description
        default_enabled: Default state when no override applies
        is_public: Whether flag is exposed in public API
        rollout_percentage: Default rollout percentage (0-100)
        deprecated: Whether flag is deprecated
        environments: List of allowed environments, None means all
        created_at: Timestamp when flag was created
        updated_at: Timestamp when flag was last updated
    """

    key: str
    name: str
    description: str = ""
    default_enabled: bool = False
    is_public: bool = False
    rollout_percentage: int = 0
    deprecated: bool = False
    environments: list[str] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class TenantOverride:
    """Represents tenant-specific flag override.

    Attributes:
        key: Flag key this override applies to
        tenant_id: Tenant identifier
        enabled: Override enabled state (None = use default)
        rollout_percentage: Override rollout percentage (None = use default)
        enabled_for_users: List of user IDs explicitly enabled
        enabled_for_groups: List of group IDs enabled for
        updated_at: Timestamp when override was last updated
        updated_by: User who last updated the override
    """

    key: str
    tenant_id: str
    enabled: bool | None = None
    rollout_percentage: int | None = None
    enabled_for_users: list[str] = field(default_factory=list)
    enabled_for_groups: list[str] = field(default_factory=list)
    updated_at: datetime | None = None
    updated_by: str | None = None
