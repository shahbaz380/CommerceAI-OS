"""Application factory — creates configured FastAPI app instance."""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app import __version__
from app.bootstrap.lifecycle import on_shutdown, on_startup
from app.config.settings import AppSettings, get_settings
from app.infrastructure.monitoring.telemetry import instrument_app
from app.presentation.api.errors import register_exception_handlers
from app.presentation.api.v1.router import api_v1_router
from app.presentation.middleware.registration import register_middleware


def create_app(settings: AppSettings | None = None) -> FastAPI:
    """Build the FastAPI application (composition root)."""
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        await on_startup(settings)
        app.state.settings = settings
        yield
        await on_shutdown()

    docs_url = "/docs" if settings.api_docs_enabled else None
    redoc_url = "/redoc" if settings.api_docs_enabled else None
    openapi_url = f"{settings.api_prefix}/openapi.json" if settings.api_docs_enabled else None

    app = FastAPI(
        title="CommerceAI OS API",
        description="Enterprise multi-tenant eCommerce automation backend (foundation)",
        version=settings.app_version or __version__,
        lifespan=lifespan,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
    )

    register_middleware(app, settings)
    register_exception_handlers(app)

    # Health routes at root for k8s probes AND under api prefix
    app.include_router(api_v1_router)
    app.include_router(api_v1_router, prefix=settings.api_prefix)

    instrument_app(app, settings)
    return app
