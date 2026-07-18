"""Request/response access logging middleware."""

from __future__ import annotations

import time
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.infrastructure.logging.setup import get_logger

logger = get_logger("app.api")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        response: Response | None = None
        try:
            response = await call_next(request)
            return response
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            status = response.status_code if response is not None else 500
            logger.info(
                "http_request",
                method=request.method,
                path=request.url.path,
                status_code=status,
                duration_ms=duration_ms,
                query=str(request.url.query) if request.url.query else None,
            )
