"""OAuth provider framework — no live integrations.

Future providers: ebay, google, microsoft, github, amazon, shopify.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from urllib.parse import urlencode


class OAuthProvider(StrEnum):
    EBAY = "ebay"
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    GITHUB = "github"
    AMAZON = "amazon"
    SHOPIFY = "shopify"


@dataclass(slots=True, frozen=True)
class OAuthAuthorizationRequest:
    provider: OAuthProvider
    authorization_url: str
    state: str
    code_verifier: str | None = None


@dataclass(slots=True, frozen=True)
class OAuthTokenResult:
    access_token: str
    refresh_token: str | None
    expires_in: int | None
    provider_user_id: str
    email: str | None
    raw: dict[str, Any]


class OAuthProviderClient(ABC):
    provider: OAuthProvider

    @abstractmethod
    def build_authorize_url(self, *, state: str, redirect_uri: str) -> OAuthAuthorizationRequest:
        raise NotImplementedError

    @abstractmethod
    async def exchange_code(self, *, code: str, redirect_uri: str) -> OAuthTokenResult:
        raise NotImplementedError


class PlaceholderOAuthClient(OAuthProviderClient):
    """Stub client — raises until provider is implemented."""

    def __init__(self, provider: OAuthProvider) -> None:
        self.provider = provider

    def build_authorize_url(self, *, state: str, redirect_uri: str) -> OAuthAuthorizationRequest:
        # Structural URL only — not a real authorize endpoint
        query = urlencode({"state": state, "redirect_uri": redirect_uri, "provider": self.provider.value})
        return OAuthAuthorizationRequest(
            provider=self.provider,
            authorization_url=f"https://oauth.placeholder.local/{self.provider.value}/authorize?{query}",
            state=state,
        )

    async def exchange_code(self, *, code: str, redirect_uri: str) -> OAuthTokenResult:
        from app.shared.exceptions import AppError

        raise AppError(
            f"OAuth provider '{self.provider.value}' is not integrated yet",
            code="OAUTH_NOT_IMPLEMENTED",
            retryable=False,
        )


class OAuthProviderRegistry:
    def __init__(self) -> None:
        self._clients: dict[str, OAuthProviderClient] = {
            p.value: PlaceholderOAuthClient(p) for p in OAuthProvider
        }

    def get(self, provider: str) -> OAuthProviderClient:
        client = self._clients.get(provider)
        if client is None:
            from app.shared.exceptions import ValidationAppError

            raise ValidationAppError(
                f"Unknown OAuth provider: {provider}",
                details=[{"field": "provider", "issue": "unknown"}],
            )
        return client

    def list_providers(self) -> list[str]:
        return sorted(self._clients.keys())


_oauth_registry: OAuthProviderRegistry | None = None


def get_oauth_registry() -> OAuthProviderRegistry:
    global _oauth_registry
    if _oauth_registry is None:
        _oauth_registry = OAuthProviderRegistry()
    return _oauth_registry
