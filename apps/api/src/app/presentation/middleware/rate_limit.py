"""Rate limiting placeholder middleware.

Does not enforce limits yet; reserved for Redis token-bucket implementation.
"""

from __future__ import annotations

from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config.settings import get_settings
from app.infrastructure.logging.setup import get_logger

logger = get_logger("app.security")


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        settings = get_settings()
        if not settings.rate_limit_enabled:
            return await call_next(request)

        # Placeholder: log intent only; real limiter comes with Redis-backed store.
        logger.debug(
            "rate_limit_check_skipped_placeholder",
            path=request.url.path,
            limit=settings.rate_limit_default,
        )
        response = await call_next(request)
        response.headers.setdefault("X-RateLimit-Policy", settings.rate_limit_default)
        return response
