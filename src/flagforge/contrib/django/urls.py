"""URL routing for FlagForge Django API."""

from django.urls import path

from . import views

urlpatterns = [
    path("flags/", views.flag_list, name="flag-list"),
    path("admin/flags/", views.admin_flag_list, name="admin-flag-list"),
    path("admin/flags/<str:key>/", views.admin_flag_detail, name="admin-flag-detail"),
    path(
        "admin/flags/<str:key>/tenants/<str:tenant_id>/",
        views.tenant_override_detail,
        name="tenant-override-detail",
    ),
]
