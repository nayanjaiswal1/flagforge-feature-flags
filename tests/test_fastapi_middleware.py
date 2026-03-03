from unittest.mock import Mock

from fastapi import Request, Response
import pytest

from flagforge.contrib.fastapi.middleware import FlagForgeMiddleware
from flagforge.core.context import get_request_cache


@pytest.mark.asyncio
async def test_middleware_cache_lifecycle():
    # Mock call_next
    async def call_next(request):
        # Verify cache is active
        assert get_request_cache() is not None
        get_request_cache()["k"] = "v"
        return Response("ok")

    app = Mock()
    middleware = FlagForgeMiddleware(app)
    request = Mock(spec=Request)

    # Ensure cache is None before
    assert get_request_cache() is None

    await middleware.dispatch(request, call_next)

    # Ensure cache is None after
    assert get_request_cache() is None


@pytest.mark.asyncio
async def test_middleware_error_cleanup():
    async def call_next(request):
        assert get_request_cache() is not None
        raise ValueError("boom")

    app = Mock()
    middleware = FlagForgeMiddleware(app)
    request = Mock(spec=Request)

    with pytest.raises(ValueError):
        await middleware.dispatch(request, call_next)

    # Ensure cache is cleaned up even after error
    assert get_request_cache() is None
