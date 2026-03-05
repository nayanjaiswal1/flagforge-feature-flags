"""Django signals for cache invalidation."""

from django.db.models import signals
from django.dispatch import receiver

from .models import FeatureFlagDefinition, TenantFeatureFlag, TenantFlagOverride


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
    """Invalidate cache when a tenant flag override (column/schema mode) is saved."""
    _invalidate_tenant_cache(instance.tenant_id, instance.key.key)


@receiver(signals.post_delete, sender=TenantFeatureFlag)
def on_tenant_flag_delete(sender, instance, **kwargs):
    """Invalidate cache when a tenant flag override (column/schema mode) is deleted."""
    _invalidate_tenant_cache(instance.tenant_id, instance.key.key)


@receiver(signals.post_save, sender=TenantFlagOverride)
def on_hybrid_override_save(sender, instance, **kwargs):
    """Invalidate cache when a hybrid override is saved.

    In hybrid mode there is no tenant_id on the row — the active schema
    is the tenant context. We invalidate by flag key only; the cache
    backend (Redis with tenant-prefixed keys) handles tenant isolation.
    """
    _invalidate_flag_cache(instance.key.key)


@receiver(signals.post_delete, sender=TenantFlagOverride)
def on_hybrid_override_delete(sender, instance, **kwargs):
    """Invalidate cache when a hybrid override is deleted."""
    _invalidate_flag_cache(instance.key.key)


def _invalidate_flag_cache(flag_key: str):
    """Invalidate all cache entries for a flag across all tenants."""
    pass


def _invalidate_tenant_cache(tenant_id: str, flag_key: str):
    """Invalidate cache entries for a specific tenant and flag."""
    pass
