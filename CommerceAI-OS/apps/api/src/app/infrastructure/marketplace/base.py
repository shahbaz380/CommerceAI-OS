"""Marketplace adapter interface (Adapter + Strategy patterns)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(slots=True, frozen=True)
class MarketplaceContext:
    """Runtime context for adapter operations."""

    workspace_id: UUID
    connection_id: UUID | None = None
    environment: str = "sandbox"
    user_id: UUID | None = None


@dataclass(slots=True, frozen=True)
class ConnectResult:
    connection_id: UUID
    status: str
    authorization_url: str | None = None
    state: str | None = None


@dataclass(slots=True, frozen=True)
class OAuthCallbackResult:
    connection_id: UUID
    status: str
    external_account_id: str | None = None
    display_name: str | None = None


class MarketplaceAdapter(ABC):
    """Abstract adapter for a sales channel (eBay, Amazon, ...)."""

    channel: str

    @abstractmethod
    async def health(self) -> dict[str, Any]:
        """Adapter readiness metadata."""

    @abstractmethod
    async def begin_connect(self, ctx: MarketplaceContext, **kwargs: Any) -> ConnectResult:
        """Start OAuth / connection flow."""

    @abstractmethod
    async def complete_connect(
        self,
        ctx: MarketplaceContext,
        *,
        code: str,
        state: str,
        **kwargs: Any,
    ) -> OAuthCallbackResult:
        """Finish OAuth callback."""

    @abstractmethod
    async def disconnect(self, ctx: MarketplaceContext, connection_id: UUID) -> None:
        """Disconnect marketplace account."""

    @abstractmethod
    async def refresh_token(self, ctx: MarketplaceContext, connection_id: UUID) -> dict[str, Any]:
        """Refresh OAuth tokens if needed."""

    @abstractmethod
    async def validate_connection(self, ctx: MarketplaceContext, connection_id: UUID) -> dict[str, Any]:
        """Validate connection health with provider (or local checks)."""


class MarketplaceRegistry:
    """Registry of channel adapters for DI and plugins."""

    def __init__(self) -> None:
        self._adapters: dict[str, MarketplaceAdapter] = {}

    def register(self, adapter: MarketplaceAdapter) -> None:
        self._adapters[adapter.channel] = adapter

    def get(self, channel: str) -> MarketplaceAdapter | None:
        return self._adapters.get(channel)

    def require(self, channel: str) -> MarketplaceAdapter:
        adapter = self.get(channel)
        if adapter is None:
            from app.shared.exceptions import ValidationAppError

            raise ValidationAppError(
                f"Unsupported marketplace channel: {channel}",
                details=[{"field": "channel", "issue": "unsupported"}],
            )
        return adapter

    def list_channels(self) -> list[str]:
        return sorted(self._adapters.keys())

    def all(self) -> dict[str, MarketplaceAdapter]:
        return dict(self._adapters)
