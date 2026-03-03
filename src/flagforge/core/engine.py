"""Feature flag evaluation engines."""

from flagforge.cache import (
    AsyncCacheBackend,
    AsyncNullCache,
    CacheBackend,
    NullCache,
)
from flagforge.core.context import FeatureContext
from flagforge.core.resolver import resolve
from flagforge.storage.base import AsyncStorageBackend as BaseAsyncStorageBackend
from flagforge.storage.base import StorageBackend as BaseStorageBackend


class FlagEngine:
    """Synchronous feature flag evaluation engine.

    Provides methods to evaluate feature flags with caching support.

    Attributes:
        storage: Storage backend for flag definitions and overrides
        cache: Cache backend for evaluation results
    """

    def __init__(self, storage: BaseStorageBackend, cache: CacheBackend | None = None):
        """Initialize the flag engine.

        Args:
            storage: Storage backend for flag definitions and overrides
            cache: Cache backend (defaults to NullCache)
        """
        self.storage = storage
        self.cache = cache or NullCache()

    def is_enabled(self, key: str, context: FeatureContext) -> bool:
        """Check if a feature flag is enabled for the given context.

        Args:
            key: Feature flag key
            context: Evaluation context

        Returns:
            bool: Whether the flag is enabled
        """
        if context.tenant_id is None:
            raise ValueError("tenant_id is required for flag evaluation")

        # Build cache key
        cache_key = self._build_cache_key(key, context)

        # Check cache first
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        # Load definition and override
        definition = self.storage.get_definition(key)
        if definition is None:
            # Unknown keys return False
            return False

        override = self.storage.get_tenant_override(key, context.tenant_id)

        # Resolve flag
        result = resolve(definition, override, context)

        # Cache result
        self.cache.set(cache_key, result)

        return result

    def evaluate_many(
        self, keys: list[str], context: FeatureContext
    ) -> dict[str, bool]:
        """Evaluate multiple feature flags in a single round-trip.

        Unknown keys return False (not omitted, not raised).

        Args:
            keys: List of feature flag keys to evaluate
            context: Evaluation context

        Returns:
            dict[str, bool]: Mapping of flag keys to enabled state
        """
        if context.tenant_id is None:
            raise ValueError("tenant_id is required for flag evaluation")

        # Get all definitions and overrides in one round-trip
        definitions = self.storage.get_all_definitions()
        overrides = self.storage.get_all_tenant_overrides(context.tenant_id)

        # Build lookup dicts
        def_by_key = {d.key: d for d in definitions}
        override_by_key = {o.key: o for o in overrides}

        result = {}
        for key in keys:
            definition = def_by_key.get(key)
            if definition is None:
                # Unknown keys return False
                result[key] = False
                continue

            override = override_by_key.get(key)
            result[key] = resolve(definition, override, context)

        return result

    def evaluate_all(self, context: FeatureContext) -> dict[str, bool]:
        """Evaluate all defined flags for the tenant.

        Args:
            context: Evaluation context

        Returns:
            dict[str, bool]: Mapping of all flag keys to enabled state
        """
        if context.tenant_id is None:
            raise ValueError("tenant_id is required for flag evaluation")

        # Get all definitions and overrides
        definitions = self.storage.get_all_definitions()
        overrides = self.storage.get_all_tenant_overrides(context.tenant_id)

        # Build lookup dicts
        override_by_key = {o.key: o for o in overrides}

        result = {}
        for definition in definitions:
            override = override_by_key.get(definition.key)
            result[definition.key] = resolve(definition, override, context)

        return result

    def _build_cache_key(self, key: str, context: FeatureContext) -> str:
        """Build a cache key from flag key and context."""
        parts = [key, context.tenant_id or ""]
        if context.user_id:
            parts.append(context.user_id)
        if context.environment:
            parts.append(context.environment)
        return ":".join(parts)


class AsyncFlagEngine:
    """Asynchronous feature flag evaluation engine.

    Provides async methods to evaluate feature flags with caching support.

    Attributes:
        storage: Async storage backend for flag definitions and overrides
        cache: Async cache backend for evaluation results
    """

    def __init__(
        self, storage: BaseAsyncStorageBackend, cache: AsyncCacheBackend | None = None
    ):
        """Initialize the async flag engine.

        Args:
            storage: Async storage backend for flag definitions and overrides
            cache: Async cache backend (defaults to AsyncNullCache)
        """
        self.storage = storage
        self.cache = cache or AsyncNullCache()

    async def is_enabled(self, key: str, context: FeatureContext) -> bool:
        """Check if a feature flag is enabled for the given context.

        Args:
            key: Feature flag key
            context: Evaluation context

        Returns:
            bool: Whether the flag is enabled
        """
        if context.tenant_id is None:
            raise ValueError("tenant_id is required for flag evaluation")

        # Build cache key
        cache_key = self._build_cache_key(key, context)

        # Check cache first
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return cached

        # Load definition and override
        definition = await self.storage.get_definition(key)
        if definition is None:
            # Unknown keys return False
            return False

        override = await self.storage.get_tenant_override(key, context.tenant_id)

        # Resolve flag
        result = resolve(definition, override, context)

        # Cache result
        await self.cache.set(cache_key, result)

        return result

    async def evaluate_many(
        self, keys: list[str], context: FeatureContext
    ) -> dict[str, bool]:
        """Evaluate multiple feature flags in a single round-trip.

        Unknown keys return False (not omitted, not raised).

        Args:
            keys: List of feature flag keys to evaluate
            context: Evaluation context

        Returns:
            dict[str, bool]: Mapping of flag keys to enabled state
        """
        if context.tenant_id is None:
            raise ValueError("tenant_id is required for flag evaluation")

        # Get all definitions and overrides in one round-trip
        definitions = await self.storage.get_all_definitions()
        overrides = await self.storage.get_all_tenant_overrides(context.tenant_id)

        # Build lookup dicts
        def_by_key = {d.key: d for d in definitions}
        override_by_key = {o.key: o for o in overrides}

        result = {}
        for key in keys:
            definition = def_by_key.get(key)
            if definition is None:
                # Unknown keys return False
                result[key] = False
                continue

            override = override_by_key.get(key)
            result[key] = resolve(definition, override, context)

        return result

    async def evaluate_all(self, context: FeatureContext) -> dict[str, bool]:
        """Evaluate all defined flags for the tenant.

        Args:
            context: Evaluation context

        Returns:
            dict[str, bool]: Mapping of all flag keys to enabled state
        """
        if context.tenant_id is None:
            raise ValueError("tenant_id is required for flag evaluation")

        # Get all definitions and overrides
        definitions = await self.storage.get_all_definitions()
        overrides = await self.storage.get_all_tenant_overrides(context.tenant_id)

        # Build lookup dicts
        override_by_key = {o.key: o for o in overrides}

        result = {}
        for definition in definitions:
            override = override_by_key.get(definition.key)
            result[definition.key] = resolve(definition, override, context)

        return result

    def _build_cache_key(self, key: str, context: FeatureContext) -> str:
        """Build a cache key from flag key and context."""
        parts = [key, context.tenant_id or ""]
        if context.user_id:
            parts.append(context.user_id)
        if context.environment:
            parts.append(context.environment)
        return ":".join(parts)
