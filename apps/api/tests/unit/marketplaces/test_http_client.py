"""HTTP client retry/rate-limit unit tests with httpx mock transport."""

from __future__ import annotations

import httpx
import pytest

from app.infrastructure.marketplace.http.client import AsyncHttpClient, HttpRequest, RetryPolicy
from app.shared.exceptions import RateLimitError


@pytest.mark.asyncio
async def test_http_client_success() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as raw:
        client = AsyncHttpClient(client=raw, retry=RetryPolicy(max_attempts=1))
        resp = await client.request(HttpRequest(method="GET", url="https://example.test/x"))
        assert resp.status_code == 200
        assert resp.json_data == {"ok": True}


@pytest.mark.asyncio
async def test_http_client_retries_then_rate_limit() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(429, headers={"Retry-After": "0"}, json={"error": "slow down"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as raw:
        client = AsyncHttpClient(
            client=raw,
            retry=RetryPolicy(max_attempts=2, base_delay_seconds=0.01, max_delay_seconds=0.02),
        )
        with pytest.raises(RateLimitError):
            await client.request(HttpRequest(method="GET", url="https://example.test/x"))
        assert calls["n"] == 2
