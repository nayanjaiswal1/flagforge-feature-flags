from django.contrib.auth.models import User
import pytest
from rest_framework.test import APIClient

from flagforge.contrib.django.models import FeatureFlagDefinition, TenantFeatureFlag


@pytest.mark.django_db
class TestDjangoViews:
    def setup_method(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser("admin", "admin@test.com", "password")
        self.regular_user = User.objects.create_user("user", "user@test.com", "password")

        # Create some flags
        self.f1 = FeatureFlagDefinition.objects.create(
            key="public_flag", name="Public", is_public=True, default_enabled=True
        )
        self.f2 = FeatureFlagDefinition.objects.create(
            key="private_flag", name="Private", is_public=False, default_enabled=True
        )

    def test_flag_list_anonymous(self):
        # Should only see public flag
        response = self.client.get("/api/flags/?tenant_id=t1")
        assert response.status_code == 200
        assert "public_flag" in response.data
        assert "private_flag" not in response.data

    def test_flag_list_authenticated(self):
        self.client.force_authenticate(user=self.regular_user)
        # Should see all flags
        response = self.client.get("/api/flags/?tenant_id=t1")
        assert response.status_code == 200
        assert "public_flag" in response.data
        assert "private_flag" in response.data

    def test_flag_list_missing_tenant(self):
        response = self.client.get("/api/flags/")
        assert response.status_code == 400

    def test_admin_flag_list_permission(self):
        # Regular user should be forbidden
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get("/api/admin/flags/")
        assert response.status_code == 403

        # Admin should be allowed
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get("/api/admin/flags/")
        assert response.status_code == 200
        assert len(response.data) == 2

    def test_admin_flag_crud(self):
        self.client.force_authenticate(user=self.admin_user)

        # GET detail
        response = self.client.get(f"/api/admin/flags/{self.f1.key}/")
        assert response.status_code == 200
        assert response.data["key"] == self.f1.key

        # UPDATE
        response = self.client.put(f"/api/admin/flags/{self.f1.key}/", {"name": "Updated Name"})
        assert response.status_code == 200
        assert response.data["name"] == "Updated Name"

        # DELETE
        response = self.client.delete(f"/api/admin/flags/{self.f1.key}/")
        assert response.status_code == 204
        assert not FeatureFlagDefinition.objects.filter(key=self.f1.key).exists()

    def test_tenant_override_crud(self):
        self.client.force_authenticate(user=self.admin_user)

        # CREATE (PUT on non-existent)
        url = f"/api/admin/flags/{self.f2.key}/tenants/t1/"
        response = self.client.put(url, {"enabled": True})
        assert response.status_code == 200
        assert response.data["enabled"] is True
        assert TenantFeatureFlag.objects.filter(tenant_id="t1", key=self.f2).exists()

        # GET
        response = self.client.get(url)
        assert response.status_code == 200
        assert response.data["enabled"] is True

        # DELETE
        response = self.client.delete(url)
        assert response.status_code == 204
        assert not TenantFeatureFlag.objects.filter(tenant_id="t1", key=self.f2).exists()
