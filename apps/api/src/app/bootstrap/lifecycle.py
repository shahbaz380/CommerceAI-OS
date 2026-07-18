"""Startup / shutdown lifecycle hooks."""

from __future__ import annotations

from app.config.settings import AppSettings
from app.core.di.container import build_container, reset_container
from app.core.plugins.loader import get_plugin_loader
from app.infrastructure.cache.redis_client import init_redis, shutdown_redis
from app.infrastructure.database.session import (
    init_database,
    shutdown_database,
    validate_database_on_startup,
)
from app.infrastructure.logging.setup import get_logger, setup_logging
from app.infrastructure.monitoring.telemetry import setup_telemetry, shutdown_telemetry

logger = get_logger("app")


async def on_startup(settings: AppSettings) -> None:
    setup_logging(settings)
    logger.info("startup_begin", env=str(settings.app_env), version=settings.app_version)
    setup_telemetry(settings)
    init_database(settings)
    if settings.database_startup_validate or settings.is_production:
        await validate_database_on_startup(
            settings,
            strict=settings.database_startup_strict or settings.is_production,
        )
    init_redis(settings)
    build_container(settings)
    # Plugin runtime: register nothing by default; loader ready
    loader = get_plugin_loader(settings)
    loader.load_enabled()
    logger.info("startup_complete", app=settings.app_name)


async def on_shutdown() -> None:
    logger.info("shutdown_begin")
    await shutdown_redis()
    await shutdown_database()
    shutdown_telemetry()
    reset_container()
    logger.info("shutdown_complete")
