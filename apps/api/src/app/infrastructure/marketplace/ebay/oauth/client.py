"""eBay OAuth 2.0 client (authorization code + refresh).

Uses real eBay OAuth endpoints; credentials must be configured per workspace.
Does not implement business resource APIs (listings/orders/etc.).
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

from app.domain.marketplaces.enums import MarketplaceEnvironment
from app.infrastructure.marketplace.http.client import AsyncHttpClient, HttpRequest
from app.shared.exceptions import MarketplaceError, ValidationAppError

# eBay OAuth endpoints
_AUTH_URL = {
    MarketplaceEnvironment.PRODUCTION: "https://auth.ebay.com/oauth2/authorize",
    MarketplaceEnvironment.SANDBOX: "https://auth.sandbox.ebay.com/oauth2/authorize",
}
_TOKEN_URL = {
    MarketplaceEnvironment.PRODUCTION: "https://api.ebay.com/identity/v1/oauth2/token",
    MarketplaceEnvironment.SANDBOX: "https://api.sandbox.ebay.com/identity/v1/oauth2/token",
}

DEFAULT_EBAY_SCOPES = (
    "https://api.ebay.com/oauth/api_scope "
    "https://api.ebay.com/oauth/api_scope/sell.marketing.readonly "
    "https://api.ebay.com/oauth/api_scope/sell.marketing "
    "https://api.ebay.com/oauth/api_scope/sell.inventory.readonly "
    "https://api.ebay.com/oauth/api_scope/sell.inventory "
    "https://api.ebay.com/oauth/api_scope/sell.account.readonly "
    "https://api.ebay.com/oauth/api_scope/sell.account "
    "https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly "
    "https://api.ebay.com/oauth/api_scope/sell.fulfillment "
    "https://api.ebay.com/oauth/api_scope/sell.analytics.readonly"
)


@dataclass(slots=True, frozen=True)
class EbayOAuthConfig:
    client_id: str
    client_secret: str
    redirect_uri: str
    environment: str = MarketplaceEnvironment.SANDBOX
    scopes: str = DEFAULT_EBAY_SCOPES
    ru_name: str | None = None


@dataclass(slots=True, frozen=True)
class EbayTokenResponse:
    access_token: str
    refresh_token: str | None
    expires_in: int | None
    refresh_token_expires_in: int | None
    token_type: str
    scope: str | None
    raw: dict[str, Any]


class EbayOAuthClient:
    """eBay OAuth protocol client."""

    channel = "ebay"

    def __init__(self, config: EbayOAuthConfig, http: AsyncHttpClient | None = None) -> None:
        self.config = config
        self.http = http or AsyncHttpClient(timeout=30.0)
        try:
            self.env = MarketplaceEnvironment(config.environment)
        except ValueError as exc:
            raise ValidationAppError(
                "Invalid eBay environment",
                details=[{"field": "environment", "issue": config.environment}],
            ) from exc

    def build_authorization_url(self, *, state: str) -> str:
        # eBay uses redirect_uri as RuName in many app configs; support both.
        redirect = self.config.ru_name or self.config.redirect_uri
        params = {
            "client_id": self.config.client_id,
            "redirect_uri": redirect,
            "response_type": "code",
            "state": state,
            "scope": self.config.scopes,
        }
        return f"{_AUTH_URL[self.env]}?{urlencode(params)}"

    def _basic_auth_header(self) -> str:
        raw = f"{self.config.client_id}:{self.config.client_secret}".encode()
        return "Basic " + base64.b64encode(raw).decode("ascii")

    async def exchange_code(self, *, code: str) -> EbayTokenResponse:
        redirect = self.config.ru_name or self.config.redirect_uri
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect,
        }
        return await self._token_request(data)

    async def refresh(self, *, refresh_token: str) -> EbayTokenResponse:
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "scope": self.config.scopes,
        }
        return await self._token_request(data)

    async def _token_request(self, data: dict[str, str]) -> EbayTokenResponse:
        resp = await self.http.request(
            HttpRequest(
                method="POST",
                url=_TOKEN_URL[self.env],
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": self._basic_auth_header(),
                },
                data=data,
            )
        )
        if resp.status_code >= 400:
            detail = resp.json_data if isinstance(resp.json_data, dict) else {"body": resp.text}
            raise MarketplaceError(
                f"eBay token endpoint failed: HTTP {resp.status_code}",
                code="EBAY_TOKEN_ERROR",
                provider="ebay",
                provider_code=str(resp.status_code),
                retryable=resp.status_code >= 500,
                details=[{"field": "response", "issue": str(detail)[:500]}],
            )
        payload = resp.json_data if isinstance(resp.json_data, dict) else {}
        access = payload.get("access_token")
        if not access:
            raise MarketplaceError(
                "eBay token response missing access_token",
                code="EBAY_TOKEN_INVALID",
                provider="ebay",
                retryable=False,
            )
        return EbayTokenResponse(
            access_token=str(access),
            refresh_token=str(payload["refresh_token"]) if payload.get("refresh_token") else None,
            expires_in=int(payload["expires_in"]) if payload.get("expires_in") is not None else None,
            refresh_token_expires_in=(
                int(payload["refresh_token_expires_in"])
                if payload.get("refresh_token_expires_in") is not None
                else None
            ),
            token_type=str(payload.get("token_type") or "Bearer"),
            scope=str(payload["scope"]) if payload.get("scope") else None,
            raw=payload,
        )
