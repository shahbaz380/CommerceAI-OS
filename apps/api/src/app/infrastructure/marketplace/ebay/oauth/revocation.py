"""eBay token revocation helper (best-effort)."""

from __future__ import annotations

import base64
from typing import Any

from app.domain.marketplaces.enums import MarketplaceEnvironment
from app.infrastructure.logging.setup import get_logger
from app.infrastructure.marketplace.ebay.oauth.client import EbayOAuthConfig
from app.infrastructure.marketplace.http.client import AsyncHttpClient, HttpRequest

logger = get_logger("app.marketplace")

_REVOKE_URL = {
    MarketplaceEnvironment.PRODUCTION: "https://api.ebay.com/identity/v1/oauth2/revoke",
    MarketplaceEnvironment.SANDBOX: "https://api.sandbox.ebay.com/identity/v1/oauth2/revoke",
}


async def revoke_ebay_token(
    config: EbayOAuthConfig,
    *,
    token: str,
    token_type_hint: str = "refresh_token",
    http: AsyncHttpClient | None = None,
) -> dict[str, Any]:
    """Best-effort revoke. Failures are logged but not fatal for local disconnect."""
    env = MarketplaceEnvironment(config.environment)
    client = http or AsyncHttpClient(timeout=15.0)
    owns = http is None
    try:
        basic = base64.b64encode(f"{config.client_id}:{config.client_secret}".encode()).decode()
        resp = await client.request(
            HttpRequest(
                method="POST",
                url=_REVOKE_URL[env],
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": f"Basic {basic}",
                },
                data={"token": token, "token_type_hint": token_type_hint},
            )
        )
        logger.info(
            "ebay_token_revoke_attempt",
            status_code=resp.status_code,
            environment=config.environment,
        )
        return {"status_code": resp.status_code, "ok": resp.status_code < 400}
    except Exception as exc:  # noqa: BLE001
        logger.warning("ebay_token_revoke_failed", error=str(exc))
        return {"ok": False, "error": str(exc)}
    finally:
        if owns:
            await client.aclose()
