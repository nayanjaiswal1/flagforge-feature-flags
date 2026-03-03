"""Django REST Framework serializers for FlagForge."""

from rest_framework import serializers

from .models import FeatureFlagDefinition, TenantFeatureFlag


class FlagDefinitionSerializer(serializers.ModelSerializer):
    """Serializer for feature flag definitions."""

    class Meta:
        model = FeatureFlagDefinition
        fields = [
            "key",
            "name",
            "description",
            "default_enabled",
            "is_public",
            "rollout_percentage",
            "deprecated",
            "environments",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class TenantOverrideSerializer(serializers.ModelSerializer):
    """Serializer for tenant-specific flag overrides."""

    key = serializers.SlugRelatedField(
        slug_field="key", queryset=FeatureFlagDefinition.objects.all()
    )

    class Meta:
        model = TenantFeatureFlag
        fields = [
            "key",
            "tenant_id",
            "enabled",
            "rollout_percentage",
            "enabled_for_users",
            "enabled_for_groups",
            "updated_at",
            "updated_by",
        ]
        read_only_fields = ["updated_at"]
