"""Multi-tenant organization/workspace API tests."""

from __future__ import annotations


def _register(client, email: str = "owner@example.com"):
    r = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Str0ng!Passw0rd", "full_name": "Owner"},
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_create_org_workspace_invite_flow(client) -> None:
    owner = _register(client, "owner@example.com")
    headers = {"Authorization": f"Bearer {owner['access_token']}"}

    org = client.post(
        "/api/v1/organizations",
        headers=headers,
        json={"name": "Acme Corp", "slug": "acme-corp", "currency": "usd"},
    )
    assert org.status_code == 201, org.text
    org_id = org.json()["id"]
    assert org.json()["currency"] == "USD"

    workspaces = client.get(f"/api/v1/organizations/{org_id}/workspaces", headers=headers)
    assert workspaces.status_code == 200
    assert len(workspaces.json()) == 1
    default_ws = workspaces.json()[0]["id"]

    # create second workspace
    ws2 = client.post(
        f"/api/v1/organizations/{org_id}/workspaces",
        headers=headers,
        json={"name": "EU Store", "slug": "eu-store"},
    )
    assert ws2.status_code == 201
    ws2_id = ws2.json()["id"]

    inv = client.post(
        f"/api/v1/workspaces/{ws2_id}/invitations",
        headers=headers,
        json={"email": "staff@example.com", "role_code": "staff"},
    )
    assert inv.status_code == 201, inv.text
    token = inv.json()["token"]
    assert token

    staff = _register(client, "staff@example.com")
    staff_headers = {"Authorization": f"Bearer {staff['access_token']}"}
    acc = client.post(
        "/api/v1/invitations/accept",
        headers=staff_headers,
        json={"token": token},
    )
    assert acc.status_code == 200, acc.text
    assert acc.json()["role_code"] == "staff"

    # staff cannot access default workspace they are not a member of
    denied = client.get(f"/api/v1/workspaces/{default_ws}", headers=staff_headers)
    assert denied.status_code in (403, 404)

    # staff can access invited workspace
    ok = client.get(f"/api/v1/workspaces/{ws2_id}", headers=staff_headers)
    assert ok.status_code == 200

    # switch context header
    ctx = client.get(
        "/api/v1/workspaces/current",
        headers={**staff_headers, "X-Workspace-Id": ws2_id},
    )
    assert ctx.status_code == 200
    assert ctx.json()["workspace_id"] == ws2_id
    assert ctx.json()["role_code"] == "staff"

    # profile
    prof = client.patch(
        "/api/v1/profiles/me",
        headers=staff_headers,
        json={"display_name": "Staff User", "theme": "dark"},
    )
    assert prof.status_code == 200
    assert prof.json()["display_name"] == "Staff User"


def test_org_slug_unique(client) -> None:
    a = _register(client, "owner2@example.com")
    h = {"Authorization": f"Bearer {a['access_token']}"}
    r1 = client.post("/api/v1/organizations", headers=h, json={"name": "One", "slug": "same-slug"})
    assert r1.status_code == 201
    r2 = client.post("/api/v1/organizations", headers=h, json={"name": "Two", "slug": "same-slug"})
    assert r2.status_code == 409
