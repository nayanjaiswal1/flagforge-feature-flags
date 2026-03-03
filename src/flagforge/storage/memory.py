"""In-memory storage implementations."""

import asyncio

from flagforge.core.models import FlagDefinition, TenantOverride
from flagforge.storage.base import AsyncStorageBackend, StorageBackend


class InMemoryStorage(StorageBackend):
    """In-memory storage backend using dictionaries.

    Stores flag definitions and tenant overrides in memory using:
    - _definitions: dict mapping flag key to FlagDefinition
    - _overrides: dict mapping "tenant_id:flag_key" to TenantOverride
    """

    def __init__(self) -> None:
        """Initialize the in-memory storage."""
        self._definitions: dict[str, FlagDefinition] = {}
        self._overrides: dict[str, TenantOverride] = {}

    def _override_key(self, key: str, tenant_id: str) -> str:
        """Generate composite key for tenant override lookup."""
        return f"{tenant_id}:{key}"

    def get_definition(self, key: str) -> FlagDefinition | None:
        """Retrieve a flag definition by its key."""
        return self._definitions.get(key)

    def get_all_definitions(self) -> list[FlagDefinition]:
        """Retrieve all flag definitions."""
        return list(self._definitions.values())

    def get_tenant_override(self, key: str, tenant_id: str) -> TenantOverride | None:
        """Retrieve a tenant-specific override for a flag."""
        return self._overrides.get(self._override_key(key, tenant_id))

    def get_all_tenant_overrides(self, tenant_id: str) -> list[TenantOverride]:
        """Retrieve all tenant overrides for a specific tenant."""
        prefix = f"{tenant_id}:"
        return [
            override
            for composite_key, override in self._overrides.items()
            if composite_key.startswith(prefix)
        ]

    def upsert_definition(self, definition: FlagDefinition) -> None:
        """Create or update a flag definition."""
        self._definitions[definition.key] = definition

    def upsert_tenant_override(self, override: TenantOverride) -> None:
        """Create or update a tenant-specific override."""
        self._overrides[self._override_key(override.key, override.tenant_id)] = override

    def delete_tenant_override(self, key: str, tenant_id: str) -> None:
        """Delete a tenant-specific override."""
        self._overrides.pop(self._override_key(key, tenant_id), None)

    def delete_definition(self, key: str) -> None:
        """Delete a flag definition and all its tenant overrides.

        This cascades - removes the definition AND all overrides with
        the matching flag key.
        """
        # Remove the definition
        self._definitions.pop(key, None)

        # Cascade delete all tenant overrides for this flag key
        suffix = f":{key}"
        keys_to_remove = [k for k in self._overrides if k.endswith(suffix)]
        for composite_key in keys_to_remove:
            del self._overrides[composite_key]


class AsyncInMemoryStorage(AsyncStorageBackend):
    """Asynchronous in-memory storage backend.

    Same data structure as InMemoryStorage but with async/await methods.
    Uses asyncio.sleep(0) to simulate async I/O.
    """

    def __init__(self) -> None:
        """Initialize the async in-memory storage."""
        self._definitions: dict[str, FlagDefinition] = {}
        self._overrides: dict[str, TenantOverride] = {}

    def _override_key(self, key: str, tenant_id: str) -> str:
        """Generate composite key for tenant override lookup."""
        return f"{tenant_id}:{key}"

    async def get_definition(self, key: str) -> FlagDefinition | None:
        """Retrieve a flag definition by its key."""
        await asyncio.sleep(0)  # Simulate async I/O
        return self._definitions.get(key)

    async def get_all_definitions(self) -> list[FlagDefinition]:
        """Retrieve all flag definitions."""
        await asyncio.sleep(0)  # Simulate async I/O
        return list(self._definitions.values())

    async def get_tenant_override(
        self, key: str, tenant_id: str
    ) -> TenantOverride | None:
        """Retrieve a tenant-specific override for a flag."""
        await asyncio.sleep(0)  # Simulate async I/O
        return self._overrides.get(self._override_key(key, tenant_id))

    async def get_all_tenant_overrides(self, tenant_id: str) -> list[TenantOverride]:
        """Retrieve all tenant overrides for a specific tenant."""
        await asyncio.sleep(0)  # Simulate async I/O
        prefix = f"{tenant_id}:"
        return [
            override
            for composite_key, override in self._overrides.items()
            if composite_key.startswith(prefix)
        ]

    async def upsert_definition(self, definition: FlagDefinition) -> None:
        """Create or update a flag definition."""
        await asyncio.sleep(0)  # Simulate async I/O
        self._definitions[definition.key] = definition

    async def upsert_tenant_override(self, override: TenantOverride) -> None:
        """Create or update a tenant-specific override."""
        await asyncio.sleep(0)  # Simulate async I/O
        self._overrides[self._override_key(override.key, override.tenant_id)] = override

    async def delete_tenant_override(self, key: str, tenant_id: str) -> None:
        """Delete a tenant-specific override."""
        await asyncio.sleep(0)  # Simulate async I/O
        self._overrides.pop(self._override_key(key, tenant_id), None)

    async def delete_definition(self, key: str) -> None:
        """Delete a flag definition and all its tenant overrides.

        This cascades - removes the definition AND all overrides with
        the matching flag key.
        """
        await asyncio.sleep(0)  # Simulate async I/O

        # Remove the definition
        self._definitions.pop(key, None)

        # Cascade delete all tenant overrides for this flag key
        suffix = f":{key}"
        keys_to_remove = [k for k in self._overrides if k.endswith(suffix)]
        for composite_key in keys_to_remove:
            del self._overrides[composite_key]
