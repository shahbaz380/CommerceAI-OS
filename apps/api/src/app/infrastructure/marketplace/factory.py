"""Marketplace factory — builds adapters for a DB session."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.marketplaces.enums import MarketplaceChannel
from app.infrastructure.marketplace.base import MarketplaceAdapter, MarketplaceRegistry
from app.infrastructure.marketplace.ebay.adapter import EbayMarketplaceAdapter
from app.infrastructure.marketplace.http.client import AsyncHttpClient


class MarketplaceFactory:
    """Factory Pattern: create channel adapters bound to a unit-of-work session."""

    def __init__(self, session: AsyncSession, http: AsyncHttpClient | None = None) -> None:
        self.session = session
        self.http = http or AsyncHttpClient()

    def create(self, channel: str) -> MarketplaceAdapter:
        if channel == MarketplaceChannel.EBAY:
            return EbayMarketplaceAdapter(self.session, http=self.http)
        from app.shared.exceptions import ValidationAppError

        raise ValidationAppError(
            f"No adapter implementation for channel '{channel}'",
            details=[{"field": "channel", "issue": "not_implemented"}],
        )

    def build_registry(self) -> MarketplaceRegistry:
        registry = MarketplaceRegistry()
        registry.register(self.create(MarketplaceChannel.EBAY))
        # Future: registry.register(self.create(MarketplaceChannel.AMAZON))
        return registry
