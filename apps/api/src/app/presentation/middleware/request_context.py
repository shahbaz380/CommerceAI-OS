"""Request ID + correlation ID middleware."""

from __future__ import annotations

from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config.settings import get_settings
from app.core.tenancy.context import resolve_tenant_from_headers
from app.infrastructure.logging.setup import bind_request_context, clear_request_context
from app.shared.types.context import RequestContext
from app.shared.utils.ids import new_request_id

REQUEST_CONTEXT_STATE_KEY = "request_context"


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        settings = get_settings()
        request_id = request.headers.get("X-Request-Id") or new_request_id()
        correlation_id = request.headers.get("X-Correlation-Id") or request_id
        tenant_header = request.headers.get(settings.default_tenant_header)
        tenant = resolve_tenant_from_headers(
            tenant_header,
            enforcement=settings.tenancy_enforcement,
        )

        ctx = RequestContext(
            request_id=request_id,
            correlation_id=correlation_id,
            tenant=tenant,
            path=request.url.path,
            method=request.method,
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        request.state.request_context = ctx

        bind_request_context(
            request_id=request_id,
            correlation_id=correlation_id,
            workspace_id=str(tenant.workspace_id) if tenant.workspace_id else None,
            path=request.url.path,
            method=request.method,
        )
        try:
            response = await call_next(request)
        finally:
            clear_request_context()

        response.headers["X-Request-Id"] = request_id
        response.headers["X-Correlation-Id"] = correlation_id
        return response
