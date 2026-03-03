"""Django template tags for FlagForge."""

from django import template

from flagforge.contrib.django.engine import flag_enabled

register = template.Library()


@register.simple_tag(takes_context=True)
def is_flag_enabled(context, flag_key):
    """Check if a feature flag is enabled in a template.

    Usage:
        {% load flagforge %}
        {% is_flag_enabled "new_feature" as feature_on %}
        {% if feature_on %}
            ...
        {% endif %}
    """
    request = context.get("request")
    return flag_enabled(flag_key, request)


@register.filter
def flag_enabled_filter(request, flag_key):
    """Filter to check if a flag is enabled.

    Usage:
        {{ request|flag_enabled_filter:"new_feature" }}
    """
    return flag_enabled(flag_key, request)
