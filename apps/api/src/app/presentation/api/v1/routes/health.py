"""Health, readiness, liveness, version, and system info endpoints.

These are operational foundation endpoints — not business APIs.
"""

from __future__ import annotations

import platform
import sys
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Response, status

from app import __version__
from app.config.settings import AppSettings
from app.core.di.container import AppContainer
from app.presentation.api.deps.common import get_app_container, get_app_settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(settings: AppSettings = Depends(get_app_settings)) -> dict[str, Any]:
    """Aggregate health (shallow)."""
    return {
        "status": "ok",
        "service": settings.app_name,
        "env": str(settings.app_env),
        "version": settings.app_version or __version__,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/health/live")
async def liveness() -> dict[str, str]:
    """Process is up — no dependency checks."""
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness(
    response: Response,
    container: AppContainer = Depends(get_app_container),
) -> dict[str, Any]:
    """Readiness — checks DB and Redis when available; degrades status if down."""
    db_ok = await container.database.healthcheck()
    redis_ok = await container.redis.ping()
    ready = db_ok and redis_ok
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status": "ready" if ready else "not_ready",
        "checks": {
            "database": "up" if db_ok else "down",
            "redis": "up" if redis_ok else "down",
        },
        "database_pool": container.database.pool_stats().as_dict(),
    }


@router.get("/health/database")
async def database_health(
    response: Response,
    container: AppContainer = Depends(get_app_container),
) -> dict[str, Any]:
    """Detailed database connection verification + pool monitoring."""
    details = await container.database.verify_connection()
    if not details.get("ok"):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return details


@router.get("/health/version")
async def version(settings: AppSettings = Depends(get_app_settings)) -> dict[str, str]:
    return {
        "version": settings.app_version or __version__,
        "api": "v1",
        "app": settings.app_name,
    }


@router.get("/health/system")
async def system_info(settings: AppSettings = Depends(get_app_settings)) -> dict[str, Any]:
    """Non-sensitive runtime information for ops."""
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "env": str(settings.app_env),
        "debug": settings.debug,
        "features": {
            "ai_writes": settings.feature_ai_writes_enabled,
            "ebay_sync": settings.feature_ebay_sync_enabled,
            "plugins": settings.feature_plugin_runtime,
            "billing": settings.feature_billing_enabled,
        },
        "otel_enabled": settings.otel_enabled,
    }
