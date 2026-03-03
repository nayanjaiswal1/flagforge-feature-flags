"""Django app configuration for FlagForge."""

from django.apps import AppConfig


class FlagForgeDjangoConfig(AppConfig):
    """Django app configuration for FlagForge feature flags.

    Attributes:
        name: Django app name
        verbose_name: Human-readable app name
    """

    name = "flagforge.contrib.django"
    verbose_name = "Feature Flags"

    def ready(self):
        """Import signals when the app is ready."""
        from flagforge.contrib.django import signals  # noqa: F401
