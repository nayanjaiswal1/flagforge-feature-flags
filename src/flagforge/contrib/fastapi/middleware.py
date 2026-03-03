"""FastAPI middleware for FlagForge."""

from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from flagforge.core.context import async_request_context


class FlagForgeMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for request-scoped feature flag cache.

    This middleware initializes the request-local cache at the start
    of each request and ensures it's properly cleaned up.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process the request with request-local cache context."""
        async with async_request_context():
            response = await call_next(request)
        return response
