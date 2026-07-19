"""eBay OAuth API integration tests with mocked token exchange."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.infrastructure.marketplace.ebay.oauth.client import EbayTokenResponse


def _auth(client, email: str) -> dict[str, str]:
    r = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Str0ng!Passw0rd"},
    )
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _workspace(client, headers: dict[str, str], slug: str) -> str:
    org = client.post(
        "/api/v1/organizations",
        headers=headers,
        json={"name": f"Org {slug}", "slug": slug},
    )
    assert org.status_code == 201, org.text
    wss = client.get(f"/api/v1/organizations/{org.json()['id']}/workspaces", headers=headers)
    assert wss.status_code == 200
    return wss.json()[0]["id"]


def _setup_creds(client, headers: dict[str, str], ws: str) -> None:
    cred = client.post(
        f"/api/v1/marketplaces/ebay/workspaces/{ws}/credentials",
        headers=headers,
        json={
            "channel": "ebay",
            "environment": "sandbox",
            "client_id": "ebay-client",
            "client_secret": "ebay-secret",
            "redirect_uri": "https://app.example.com/oauth/ebay/callback",
            "ru_name": "RuName-Test",
        },
    )
    assert cred.status_code == 201, cred.text


def test_ebay_connect_url_and_callback_mocked(client) -> None:
    headers = _auth(client, "ebay1@example.com")
    ws = _workspace(client, headers, "ebay-ws-1")
    _setup_creds(client, headers, ws)

    start = client.get(
        f"/api/v1/marketplaces/ebay/workspaces/{ws}/connect",
        headers=headers,
        params={"environment": "sandbox", "display_name": "Seller A", "alias": "primary"},
    )
    assert start.status_code == 200, start.text
    data = start.json()
    assert data["authorization_url"]
    assert "auth.sandbox.ebay.com" in data["authorization_url"]
    assert data["state"]
    connection_id = data["connection_id"]
    state = data["state"]

    token = EbayTokenResponse(
        access_token="access-token-value",
        refresh_token="refresh-token-value",
        expires_in=7200,
        refresh_token_expires_in=86_400,
        token_type="User Access Token",
        scope="scope",
        raw={"access_token": "access-token-value"},
    )

    with (
        patch(
            "app.infrastructure.marketplace.ebay.oauth.client.EbayOAuthClient.exchange_code",
            new=AsyncMock(return_value=token),
        ),
        patch(
            "app.infrastructure.marketplace.ebay.client.gateway.EbayApiGateway.get_user_account_summary",
            new=AsyncMock(
                return_value={
                    "user_id": "ebay-user-1",
                    "username": "test_seller",
                    "registration_marketplace_id": "EBAY_US",
                }
            ),
        ),
    ):
        cb = client.post(
            f"/api/v1/marketplaces/ebay/workspaces/{ws}/callback",
            headers=headers,
            json={"code": "auth-code", "state": state, "connection_id": connection_id},
        )
    assert cb.status_code == 200, cb.text
    assert cb.json()["status"] == "connected"
    assert cb.json()["external_account_id"] == "ebay-user-1"
    assert cb.json()["display_name"] == "test_seller"

    # replay state fails
    with patch(
        "app.infrastructure.marketplace.ebay.oauth.client.EbayOAuthClient.exchange_code",
        new=AsyncMock(return_value=token),
    ):
        replay = client.post(
            f"/api/v1/marketplaces/ebay/workspaces/{ws}/callback",
            headers=headers,
            json={"code": "auth-code", "state": state, "connection_id": connection_id},
        )
    assert replay.status_code in (400, 422)

    accounts = client.get(f"/api/v1/marketplaces/ebay/workspaces/{ws}/accounts", headers=headers)
    assert accounts.status_code == 200
    assert len(accounts.json()) == 1
    assert accounts.json()[0]["is_default"] is True
    assert accounts.json()[0]["external_username"] == "test_seller"

    status = client.get(f"/api/v1/marketplaces/ebay/workspaces/{ws}/status", headers=headers)
    assert status.status_code == 200
    assert status.json()["connected_accounts"] == 1

    # refresh
    refresh_token = EbayTokenResponse(
        access_token="access-2",
        refresh_token="refresh-2",
        expires_in=7200,
        refresh_token_expires_in=None,
        token_type="User Access Token",
        scope="scope",
        raw={},
    )
    with patch(
        "app.infrastructure.marketplace.ebay.oauth.client.EbayOAuthClient.refresh",
        new=AsyncMock(return_value=refresh_token),
    ):
        ref = client.post(
            f"/api/v1/marketplaces/ebay/workspaces/{ws}/accounts/{connection_id}/refresh",
            headers=headers,
            json={"force": True},
        )
    assert ref.status_code == 200, ref.text
    assert ref.json()["status"] in {"refreshed", "not_needed"}

    # disconnect
    disc = client.post(
        f"/api/v1/marketplaces/ebay/workspaces/{ws}/accounts/{connection_id}/disconnect",
        headers=headers,
    )
    assert disc.status_code == 200

    # reconnect starts oauth again
    recon = client.post(
        f"/api/v1/marketplaces/ebay/workspaces/{ws}/accounts/{connection_id}/reconnect",
        headers=headers,
        json={},
    )
    assert recon.status_code == 200, recon.text
    assert recon.json()["authorization_url"]


def test_ebay_oauth_error_callback(client) -> None:
    headers = _auth(client, "ebay2@example.com")
    ws = _workspace(client, headers, "ebay-ws-2")
    _setup_creds(client, headers, ws)
    start = client.get(
        f"/api/v1/marketplaces/ebay/workspaces/{ws}/connect",
        headers=headers,
    )
    state = start.json()["state"]
    bad = client.post(
        f"/api/v1/marketplaces/ebay/workspaces/{ws}/callback",
        headers=headers,
        json={"state": state, "error": "access_denied", "error_description": "user denied"},
    )
    assert bad.status_code == 400
