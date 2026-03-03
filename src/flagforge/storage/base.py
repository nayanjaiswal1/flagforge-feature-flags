"""Storage backend abstractions."""

from abc import ABC, abstractmethod

from flagforge.core.models import FlagDefinition, TenantOverride


class StorageBackend(ABC):
    """Abstract base class for synchronous storage backends.

    Defines the interface for all storage implementations that persist
    flag definitions and tenant overrides.
    """

    @abstractmethod
    def get_definition(self, key: str) -> FlagDefinition | None:
        """Retrieve a flag definition by its key.

        Args:
            key: The unique identifier for the flag

        Returns:
            FlagDefinition if found, None otherwise
        """
        pass

    @abstractmethod
    def get_all_definitions(self) -> list[FlagDefinition]:
        """Retrieve all flag definitions.

        Returns:
            List of all FlagDefinition objects
        """
        pass

    @abstractmethod
    def get_tenant_override(self, key: str, tenant_id: str) -> TenantOverride | None:
        """Retrieve a tenant-specific override for a flag.

        Args:
            key: The flag key
            tenant_id: The tenant identifier

        Returns:
            TenantOverride if found, None otherwise
        """
        pass

    @abstractmethod
    def get_all_tenant_overrides(self, tenant_id: str) -> list[TenantOverride]:
        """Retrieve all tenant overrides for a specific tenant.

        Args:
            tenant_id: The tenant identifier

        Returns:
            List of TenantOverride objects for the tenant
        """
        pass

    @abstractmethod
    def upsert_definition(self, definition: FlagDefinition) -> None:
        """Create or update a flag definition.

        Args:
            definition: The FlagDefinition to persist
        """
        pass

    @abstractmethod
    def upsert_tenant_override(self, override: TenantOverride) -> None:
        """Create or update a tenant-specific override.

        Args:
            override: The TenantOverride to persist
        """
        pass

    @abstractmethod
    def delete_tenant_override(self, key: str, tenant_id: str) -> None:
        """Delete a tenant-specific override.

        Args:
            key: The flag key
            tenant_id: The tenant identifier
        """
        pass

    @abstractmethod
    def delete_definition(self, key: str) -> None:
        """Delete a flag definition and all its tenant overrides.

        This method must cascade - deleting a definition should also
        delete all tenant overrides associated with that flag key.

        Args:
            key: The flag key to delete
        """
        pass


class AsyncStorageBackend(ABC):
    """Abstract base class for asynchronous storage backends.

    Defines the interface for async storage implementations that persist
    flag definitions and tenant overrides.
    """

    @abstractmethod
    async def get_definition(self, key: str) -> FlagDefinition | None:
        """Retrieve a flag definition by its key.

        Args:
            key: The unique identifier for the flag

        Returns:
            FlagDefinition if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_all_definitions(self) -> list[FlagDefinition]:
        """Retrieve all flag definitions.

        Returns:
            List of all FlagDefinition objects
        """
        pass

    @abstractmethod
    async def get_tenant_override(
        self, key: str, tenant_id: str
    ) -> TenantOverride | None:
        """Retrieve a tenant-specific override for a flag.

        Args:
            key: The flag key
            tenant_id: The tenant identifier

        Returns:
            TenantOverride if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_all_tenant_overrides(self, tenant_id: str) -> list[TenantOverride]:
        """Retrieve all tenant overrides for a specific tenant.

        Args:
            tenant_id: The tenant identifier

        Returns:
            List of TenantOverride objects for the tenant
        """
        pass

    @abstractmethod
    async def upsert_definition(self, definition: FlagDefinition) -> None:
        """Create or update a flag definition.

        Args:
            definition: The FlagDefinition to persist
        """
        pass

    @abstractmethod
    async def upsert_tenant_override(self, override: TenantOverride) -> None:
        """Create or update a tenant-specific override.

        Args:
            override: The TenantOverride to persist
        """
        pass

    @abstractmethod
    async def delete_tenant_override(self, key: str, tenant_id: str) -> None:
        """Delete a tenant-specific override.

        Args:
            key: The flag key
            tenant_id: The tenant identifier
        """
        pass

    @abstractmethod
    async def delete_definition(self, key: str) -> None:
        """Delete a flag definition and all its tenant overrides.

        This method must cascade - deleting a definition should also
        delete all tenant overrides associated with that flag key.

        Args:
            key: The flag key to delete
        """
        pass
