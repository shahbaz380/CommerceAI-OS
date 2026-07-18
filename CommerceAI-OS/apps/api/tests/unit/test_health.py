"""Health endpoint foundation tests."""

from __future__ import annotations


def test_liveness(client) -> None:
    res = client.get("/health/live")
    assert res.status_code == 200
    assert res.json()["status"] == "alive"
    assert "X-Request-Id" in res.headers


def test_health(client) -> None:
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_version(client) -> None:
    res = client.get("/health/version")
    assert res.status_code == 200
    assert res.json()["api"] == "v1"


def test_system(client) -> None:
    res = client.get("/health/system")
    assert res.status_code == 200
    assert "features" in res.json()


def test_health_under_api_prefix(client) -> None:
    res = client.get("/api/v1/health/live")
    assert res.status_code == 200
