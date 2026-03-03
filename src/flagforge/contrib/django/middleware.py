"""Django middleware for request-scoped cache."""

from flagforge.core.context import request_context


class RequestCacheMiddleware:
    """Django middleware for request-scoped feature flag cache.

    This middleware initializes the request-local cache at the start
    of each request and clears it at the end.
    """

    def __init__(self, get_response):
        """Initialize middleware.

        Args:
            get_response: Django's get_response callable
        """
        self.get_response = get_response

    def __call__(self, request):
        """Process the request with request-local cache context."""
        with request_context():
            response = self.get_response(request)
        return response
