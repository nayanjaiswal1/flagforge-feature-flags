"""Django signals for cache invalidation."""

from django.db.models import signals
from django.dispatch import receiver

from .models import FeatureFlagDefinition, TenantFeatureFlag


@receiver(signals.post_save, sender=FeatureFlagDefinition)
def on_flag_definition_save(sender, instance, **kwargs):
    """Invalidate cache when a flag definition is saved."""
    _invalidate_flag_cache(instance.key)


@receiver(signals.post_delete, sender=FeatureFlagDefinition)
def on_flag_definition_delete(sender, instance, **kwargs):
    """Invalidate cache when a flag definition is deleted."""
    _invalidate_flag_cache(instance.key)


@receiver(signals.post_save, sender=TenantFeatureFlag)
def on_tenant_flag_save(sender, instance, **kwargs):
    """Invalidate cache when a tenant flag is saved."""
    _invalidate_tenant_cache(instance.tenant_id, instance.key.key)


@receiver(signals.post_delete, sender=TenantFeatureFlag)
def on_tenant_flag_delete(sender, instance, **kwargs):
    """Invalidate cache when a tenant flag is deleted."""
    _invalidate_tenant_cache(instance.tenant_id, instance.key.key)


def _invalidate_flag_cache(flag_key: str):
    """Invalidate all cache entries for a flag across all tenants.

    Note: For LocalCache (request-scoped), this is a no-op since the cache
    is cleared per-request anyway. For Redis cache, this would need to use
    Redis-based invalidation. This is a placeholder for future implementation.
    """
    pass


def _invalidate_tenant_cache(tenant_id: str, flag_key: str):
    """Invalidate cache entries for a specific tenant and flag.

    Note: For LocalCache (request-scoped), this is a no-op since the cache
    is cleared per-request anyway. For Redis cache, this would need to use
    Redis-based invalidation. This is a placeholder for future implementation.
    """
    pass
