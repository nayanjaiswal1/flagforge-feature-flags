"""Django REST Framework views for FlagForge."""

from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from flagforge.core.context import FeatureContext

from .models import FeatureFlagDefinition, TenantFeatureFlag
from .serializers import FlagDefinitionSerializer, TenantOverrideSerializer

_engine = None


def _get_engine():
    """Get or create a singleton FlagEngine instance."""
    global _engine
    if _engine is None:
        from flagforge.cache import LocalCache
        from flagforge.contrib.django.storage import DjangoStorageAdapter
        from flagforge.core.engine import FlagEngine

        storage = DjangoStorageAdapter()
        cache = LocalCache()
        _engine = FlagEngine(storage=storage, cache=cache)
    return _engine


class FlagViewSet(viewsets.ModelViewSet):
    """ViewSet for feature flag definitions (admin only)."""

    queryset = FeatureFlagDefinition.objects.all()
    serializer_class = FlagDefinitionSerializer
    permission_classes = [IsAdminUser]
    lookup_field = "key"


class TenantOverrideViewSet(viewsets.ModelViewSet):
    """ViewSet for tenant-specific flag overrides (admin only)."""

    queryset = TenantFeatureFlag.objects.all()
    serializer_class = TenantOverrideSerializer
    permission_classes = [IsAdminUser]


@api_view(["GET"])
@permission_classes([AllowAny])
def flag_list(request):
    """List all resolved flags for the current user/tenant.

    Authenticated users see all flags; anonymous users see only public flags.
    """
    engine = _get_engine()

    # Get tenant from request or query params
    tenant_id = getattr(request, "tenant_id", request.GET.get("tenant_id"))

    if not tenant_id:
        return Response({"error": "tenant_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    user_id = str(request.user.id) if request.user.is_authenticated else None

    context = FeatureContext(
        tenant_id=tenant_id,
        user_id=user_id,
        environment=getattr(request, "environment", None),
    )

    if request.user.is_authenticated:
        flags = engine.evaluate_all(context)
    else:
        public_flags = FeatureFlagDefinition.objects.filter(is_public=True)
        flags = engine.evaluate_many([f.key for f in public_flags], context)

    return Response(flags)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def admin_flag_list(request):
    """List all raw flag definitions (admin only)."""
    flags = FeatureFlagDefinition.objects.all()
    serializer = FlagDefinitionSerializer(flags, many=True)
    return Response(serializer.data)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([IsAdminUser])
def admin_flag_detail(request, key):
    """CRUD operations on a specific flag definition (admin only)."""
    try:
        flag = FeatureFlagDefinition.objects.get(key=key)
    except FeatureFlagDefinition.DoesNotExist:
        return Response({"error": f"Flag '{key}' not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        serializer = FlagDefinitionSerializer(flag)
        return Response(serializer.data)

    elif request.method == "PUT":
        serializer = FlagDefinitionSerializer(flag, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == "DELETE":
        flag.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([IsAdminUser])
def tenant_override_detail(request, key, tenant_id):
    """CRUD operations on a tenant override (admin only)."""
    try:
        override = TenantFeatureFlag.objects.get(key__key=key, tenant_id=tenant_id)
    except TenantFeatureFlag.DoesNotExist:
        if request.method == "GET":
            return Response(
                {"error": f"Override for '{key}' tenant '{tenant_id}' not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        override = None

    if request.method == "GET":
        serializer = TenantOverrideSerializer(override)
        return Response(serializer.data)

    elif request.method == "PUT":
        if override:
            serializer = TenantOverrideSerializer(override, data=request.data, partial=True)
        else:
            data = request.data.copy()
            data["key"] = key
            data["tenant_id"] = tenant_id
            serializer = TenantOverrideSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == "DELETE":
        if override:
            override.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
