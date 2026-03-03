from flagforge.contrib.django.middleware import RequestCacheMiddleware
from flagforge.core.context import get_request_cache


def test_request_cache_middleware():
    def get_response(request):
        # Cache should be active during the request
        assert get_request_cache() is not None
        return "response"

    middleware = RequestCacheMiddleware(get_response)

    assert get_request_cache() is None
    middleware("fake-request")
    assert get_request_cache() is None
