"""Lightweight composition root / DI container.

Wires infrastructure adapters for FastAPI Depends without a heavy DI framework.
Swap implementations here for tests and future microservices.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.config.settings import AppSettings, get_settings
from app.core.events.bus import EventBus, get_event_bus
from app.core.plugins.loader import PluginLoader, get_plugin_loader
from app.infrastructure.ai.gateway import AIGateway, get_ai_gateway
from app.infrastructure.cache.redis_client import RedisClient, get_redis_client
from app.infrastructure.database.session import Database, get_database
from app.infrastructure.marketplace.base import MarketplaceRegistry
from app.infrastructure.marketplace.registry import get_marketplace_registry  # process registry


@dataclass
class AppContainer:
    """Application service locator / composition root."""

    settings: AppSettings
    database: Database
    redis: RedisClient
    event_bus: EventBus
    plugins: PluginLoader
    ai_gateway: AIGateway
    marketplaces: MarketplaceRegistry


_container: AppContainer | None = None


def build_container(settings: AppSettings | None = None) -> AppContainer:
    settings = settings or get_settings()
    return AppContainer(
        settings=settings,
        database=get_database(),
        redis=get_redis_client(),
        event_bus=get_event_bus(),
        plugins=get_plugin_loader(settings),
        ai_gateway=get_ai_gateway(settings),
        marketplaces=get_marketplace_registry(),
    )


def get_container() -> AppContainer:
    global _container
    if _container is None:
        _container = build_container()
    return _container


def reset_container() -> None:
    """Test helper."""
    global _container
    _container = None
