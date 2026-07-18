"""Marketplace integration infrastructure."""

from app.infrastructure.marketplace.base import (
    ConnectResult,
    MarketplaceAdapter,
    MarketplaceContext,
    MarketplaceRegistry,
    OAuthCallbackResult,
)
from app.infrastructure.marketplace.factory import MarketplaceFactory
from app.infrastructure.marketplace.registry import build_default_registry, get_marketplace_registry

__all__ = [
    "ConnectResult",
    "MarketplaceAdapter",
    "MarketplaceContext",
    "MarketplaceFactory",
    "MarketplaceRegistry",
    "OAuthCallbackResult",
    "build_default_registry",
    "get_marketplace_registry",
]
