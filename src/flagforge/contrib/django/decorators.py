"""Django decorators for feature flag protection."""

from functools import wraps

from django.http import Http404

from flagforge.contrib.django.engine import flag_enabled


def flag_required(flag_key: str, redirect_to: str | None = None):
    """Decorator to require a feature flag to be enabled.

    Args:
        flag_key: The feature flag key to check
        redirect_to: Optional URL to redirect to if flag is disabled

    Returns:
        Decorated function

    Raises:
        Http404: If flag is disabled and no redirect_to is specified
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            is_enabled = flag_enabled(flag_key, request)

            if not is_enabled:
                if redirect_to:
                    from django.shortcuts import redirect

                    return redirect(redirect_to)
                else:
                    raise Http404(f"Feature flag '{flag_key}' is not enabled")

            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator
