"""Marketplace foundation API tests (credentials + connect start + webhook)."""

from __future__ import annotations


def _auth_headers(client, email: str = "mkt@example.com") -> dict[str, str]:
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Str0ng!Passw0rd"},
    )
    assert reg.status_code == 201, reg.text
    return {"Authorization": f"Bearer {reg.json()['access_token']}"}


def _workspace(client, headers: dict[str, str]) -> str:
    org = client.post(
        "/api/v1/organizations",
        headers=headers,
        json={"name": "Market Org", "slug": f"market-org-{headers['Authorization'][-8:]}"},
    )
    # slug may collide if same suffix — use unique via random from token
    if org.status_code == 409:
        org = client.post(
            "/api/v1/organizations",
            headers=headers,
            json={"name": "Market Org 2", "slug": "market-org-unique-2"},
        )
    assert org.status_code == 201, org.text
    org_id = org.json()["id"]
    wss = client.get(f"/api/v1/organizations/{org_id}/workspaces", headers=headers)
    assert wss.status_code == 200
    return wss.json()[0]["id"]


def test_list_channels(client) -> None:
    headers = _auth_headers(client, "ch@example.com")
    res = client.get("/api/v1/marketplaces/channels", headers=headers)
    assert res.status_code == 200
    channels = {c["channel"] for c in res.json()}
    assert "ebay" in channels


def test_credentials_and_connect_start(client) -> None:
    headers = _auth_headers(client, "conn@example.com")
    ws = _workspace(client, headers)

    cred = client.post(
        f"/api/v1/marketplaces/workspaces/{ws}/credentials",
        headers=headers,
        json={
            "channel": "ebay",
            "environment": "sandbox",
            "client_id": "ebay-client-id",
            "client_secret": "ebay-client-secret",
            "redirect_uri": "https://app.example.com/oauth/ebay/callback",
            "ru_name": "MyRuName",
            "label": "sandbox app",
        },
    )
    assert cred.status_code == 201, cred.text
    body = cred.json()
    assert body["client_id"] == "ebay-client-id"
    assert "client_secret" not in body

    start = client.post(
        f"/api/v1/marketplaces/workspaces/{ws}/connect",
        headers=headers,
        json={"channel": "ebay", "environment": "sandbox", "display_name": "My eBay"},
    )
    assert start.status_code == 201, start.text
    data = start.json()
    assert data["status"] == "pending"
    assert data["authorization_url"]
    assert "auth.sandbox.ebay.com" in data["authorization_url"]
    assert data["state"]

    listing = client.get(f"/api/v1/marketplaces/workspaces/{ws}/connections", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1
    assert listing.json()[0]["status"] == "pending"

    # validate pending connection (no token yet)
    cid = data["connection_id"]
    val = client.get(
        f"/api/v1/marketplaces/workspaces/{ws}/connections/{cid}/validate",
        headers=headers,
    )
    assert val.status_code == 200
    assert val.json()["valid"] is False


def test_webhook_receive(client) -> None:
    res = client.post(
        "/api/v1/marketplaces/webhooks/ebay",
        json={"metadata": {"topic": "ORDER.CREATED"}, "notification": {"id": "1"}},
    )
    assert res.status_code == 202, res.text
    assert res.json()["channel"] == "ebay"
    assert res.json()["processed"] is False
