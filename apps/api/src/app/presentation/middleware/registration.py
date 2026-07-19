"""Register middleware in the correct order."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.config.settings import AppSettings
from app.presentation.middleware.logging import RequestLoggingMiddleware
from app.presentation.middleware.rate_limit import RateLimitMiddleware
from app.presentation.middleware.request_context import RequestContextMiddleware
from app.presentation.middleware.security_headers import SecurityHeadersMiddleware


def register_middleware(app: FastAPI, settings: AppSettings) -> None:
    """Order: outer → inner (last added is outermost for BaseHTTPMiddleware stack).

    Starlette executes user middleware in reverse addition order for BaseHTTPMiddleware.
    We add in reverse of desired execution so request flow is:
    TrustedHost → CORS → GZip → SecurityHeaders → RateLimit → RequestContext → Logging → app
    """
    # Innermost first
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(GZipMiddleware, minimum_size=500)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-Id", "X-Correlation-Id"],
    )
    if settings.allowed_hosts and settings.allowed_hosts != ["*"]:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
