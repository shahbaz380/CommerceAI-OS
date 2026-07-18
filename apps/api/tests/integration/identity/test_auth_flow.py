"""End-to-end identity API tests against in-memory SQLite."""

from __future__ import annotations


def test_register_login_me_refresh_logout(client) -> None:
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": "owner@example.com",
            "password": "Str0ng!Passw0rd",
            "full_name": "Owner One",
            "username": "owner1",
        },
    )
    assert reg.status_code == 201, reg.text
    body = reg.json()
    assert "access_token" in body
    assert body["user"]["email"] == "owner@example.com"
    assert "organization_owner" in body["user"]["roles"]
    access = body["access_token"]
    refresh = body["refresh_token"]

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access}"})
    assert me.status_code == 200
    assert me.json()["email"] == "owner@example.com"

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "owner@example.com", "password": "Str0ng!Passw0rd", "remember_me": True},
    )
    assert login.status_code == 200
    refresh2 = login.json()["refresh_token"]

    refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh2})
    assert refreshed.status_code == 200
    new_access = refreshed.json()["access_token"]

    sessions = client.get(
        "/api/v1/auth/sessions",
        headers={"Authorization": f"Bearer {new_access}"},
    )
    assert sessions.status_code == 200
    assert len(sessions.json()) >= 1

    out = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {new_access}"},
        json={"refresh_token": refreshed.json()["refresh_token"], "all_devices": True},
    )
    assert out.status_code == 200


def test_login_bad_password(client) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"email": "u2@example.com", "password": "Str0ng!Passw0rd"},
    )
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "u2@example.com", "password": "WrongPassword1!"},
    )
    assert res.status_code == 401


def test_permission_endpoint_requires_auth(client) -> None:
    res = client.get("/api/v1/identity/roles")
    assert res.status_code == 401


def test_roles_list_authenticated(client) -> None:
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": "u3@example.com", "password": "Str0ng!Passw0rd"},
    )
    token = reg.json()["access_token"]
    res = client.get("/api/v1/identity/roles", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    codes = {r["code"] for r in res.json()}
    assert "organization_owner" in codes
    assert "super_admin" in codes


def test_oauth_providers_framework(client) -> None:
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": "u4@example.com", "password": "Str0ng!Passw0rd"},
    )
    token = reg.json()["access_token"]
    res = client.get(
        "/api/v1/identity/oauth/providers",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert "ebay" in res.json()["providers"]
