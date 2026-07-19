"""eBay REST API gateway foundation (no business resource methods)."""

from __future__ import annotations

from typing import Any

from app.domain.marketplaces.enums import MarketplaceEnvironment
from app.infrastructure.marketplace.gateway.base import (
    BaseMarketplaceGateway,
    GatewayRequest,
    GatewayResponse,
)
from app.infrastructure.marketplace.http.client import AsyncHttpClient, translate_http_error

_API_BASE = {
    MarketplaceEnvironment.PRODUCTION: "https://api.ebay.com",
    MarketplaceEnvironment.SANDBOX: "https://api.sandbox.ebay.com",
}


class EbayApiGateway(BaseMarketplaceGateway):
    """Thin gateway for identity/token-adjacent and future Sell APIs."""

    def __init__(
        self,
        *,
        environment: str = MarketplaceEnvironment.SANDBOX,
        http: AsyncHttpClient | None = None,
    ) -> None:
        env = MarketplaceEnvironment(environment)
        super().__init__(
            base_url=_API_BASE[env],
            http=http or AsyncHttpClient(timeout=30.0),
            channel="ebay",
        )
        self.environment = env

    async def get(
        self,
        path: str,
        *,
        access_token: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> GatewayResponse:
        return await self.execute(
            GatewayRequest(
                method="GET",
                path=path,
                params=params,
                headers=headers or {},
                auth_bearer=access_token,
            )
        )

    async def request_with_error_translation(self, request: GatewayRequest) -> GatewayResponse:
        resp = await self.execute(request)
        if resp.status_code >= 400:
            # Rebuild HttpResponse-like mapping
            from app.infrastructure.marketplace.http.client import HttpResponse

            http_resp = HttpResponse(
                status_code=resp.status_code,
                headers=resp.headers,
                text=resp.raw_text,
                json_data=resp.data if isinstance(resp.data, dict) else None,
                duration_ms=resp.duration_ms,
                url=self.build_url(request.path),
                method=request.method,
            )
            raise translate_http_error("ebay", http_resp)
        return resp

    async def commerce_identity_user(self, access_token: str) -> dict[str, Any]:
        """Identity probe — username / userId for connection metadata only."""
        resp = await self.request_with_error_translation(
            GatewayRequest(
                method="GET",
                path="/commerce/identity/v1/user/",
                auth_bearer=access_token,
            )
        )
        return resp.data if isinstance(resp.data, dict) else {"raw": resp.data}

    async def get_user_account_summary(self, access_token: str) -> dict[str, Any]:
        """Normalize identity payload for connection health displays."""
        profile = await self.commerce_identity_user(access_token)
        return {
            "user_id": profile.get("userId") or profile.get("userAccount", {}).get("id"),
            "username": profile.get("username") or profile.get("userAccount", {}).get("loginName"),
            "registration_marketplace_id": profile.get("registrationMarketplaceId"),
            "account_type": profile.get("accountType"),
            "raw_keys": sorted(profile.keys()) if isinstance(profile, dict) else [],
        }
