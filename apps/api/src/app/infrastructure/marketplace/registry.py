"""Default process-level marketplace registry (stateless health adapters).

Session-bound adapters for OAuth should be created via MarketplaceFactory.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.domain.marketplaces.enums import MarketplaceChannel
from app.infrastructure.marketplace.base import (
    ConnectResult,
    MarketplaceAdapter,
    MarketplaceContext,
    MarketplaceRegistry,
    OAuthCallbackResult,
)


class StatelessHealthAdapter(MarketplaceAdapter):
    """Placeholder non-session adapter for registry listing/health only."""

    def __init__(self, channel: str) -> None:
        self.channel = channel

    async def health(self) -> dict[str, Any]:
        return {
            "channel": self.channel,
            "status": "registered",
            "session_bound": False,
            "note": "Use MarketplaceFactory for OAuth operations",
        }

    async def begin_connect(self, ctx: MarketplaceContext, **kwargs: Any) -> ConnectResult:
        from app.shared.exceptions import AppError

        raise AppError(
            "Session-bound adapter required; use MarketplaceFactory",
            code="ADAPTER_SESSION_REQUIRED",
            retryable=False,
        )

    async def complete_connect(
        self, ctx: MarketplaceContext, *, code: str, state: str, **kwargs: Any
    ) -> OAuthCallbackResult:
        from app.shared.exceptions import AppError

        raise AppError(
            "Session-bound adapter required; use MarketplaceFactory",
            code="ADAPTER_SESSION_REQUIRED",
            retryable=False,
        )

    async def disconnect(self, ctx: MarketplaceContext, connection_id: UUID) -> None:
        from app.shared.exceptions import AppError

        raise AppError(
            "Session-bound adapter required; use MarketplaceFactory",
            code="ADAPTER_SESSION_REQUIRED",
            retryable=False,
        )

    async def refresh_token(self, ctx: MarketplaceContext, connection_id: UUID) -> dict[str, Any]:
        from app.shared.exceptions import AppError

        raise AppError(
            "Session-bound adapter required; use MarketplaceFactory",
            code="ADAPTER_SESSION_REQUIRED",
            retryable=False,
        )

    async def validate_connection(self, ctx: MarketplaceContext, connection_id: UUID) -> dict[str, Any]:
        from app.shared.exceptions import AppError

        raise AppError(
            "Session-bound adapter required; use MarketplaceFactory",
            code="ADAPTER_SESSION_REQUIRED",
            retryable=False,
        )


_registry: MarketplaceRegistry | None = None


def build_default_registry() -> MarketplaceRegistry:
    registry = MarketplaceRegistry()
    registry.register(StatelessHealthAdapter(MarketplaceChannel.EBAY))
    return registry


def get_marketplace_registry() -> MarketplaceRegistry:
    global _registry
    if _registry is None:
        _registry = build_default_registry()
    return _registry
