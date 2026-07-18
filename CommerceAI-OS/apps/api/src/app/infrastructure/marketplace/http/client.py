"""Async HTTP client with retry, timeout, and rate-limit awareness."""

from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.infrastructure.logging.setup import get_logger
from app.shared.exceptions import DependencyError, MarketplaceError, RateLimitError

logger = get_logger("app.marketplace")


@dataclass(slots=True)
class HttpRequest:
    method: str
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    params: dict[str, Any] | None = None
    json_body: dict[str, Any] | None = None
    data: dict[str, Any] | str | None = None
    timeout: float | None = None


@dataclass(slots=True)
class HttpResponse:
    status_code: int
    headers: dict[str, str]
    text: str
    json_data: Any | None
    duration_ms: int
    url: str
    method: str


@dataclass(slots=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay_seconds: float = 0.5
    max_delay_seconds: float = 8.0
    retry_statuses: tuple[int, ...] = (408, 425, 429, 500, 502, 503, 504)


class AsyncHttpClient:
    """Shared async HTTP client for marketplace gateways."""

    def __init__(
        self,
        *,
        timeout: float = 30.0,
        retry: RetryPolicy | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._timeout = timeout
        self._retry = retry or RetryPolicy()
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            follow_redirects=False,
            headers={"User-Agent": "CommerceAI-OS/1.0"},
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def request(self, req: HttpRequest) -> HttpResponse:
        attempt = 0
        last_exc: Exception | None = None
        while attempt < self._retry.max_attempts:
            attempt += 1
            start = time.perf_counter()
            try:
                response = await self._client.request(
                    req.method.upper(),
                    req.url,
                    headers=req.headers,
                    params=req.params,
                    json=req.json_body,
                    data=req.data,
                    timeout=req.timeout or self._timeout,
                )
                duration_ms = int((time.perf_counter() - start) * 1000)
                json_data = None
                ctype = response.headers.get("content-type", "")
                if "application/json" in ctype:
                    try:
                        json_data = response.json()
                    except Exception:
                        json_data = None
                http_resp = HttpResponse(
                    status_code=response.status_code,
                    headers={k: v for k, v in response.headers.items()},
                    text=response.text,
                    json_data=json_data,
                    duration_ms=duration_ms,
                    url=str(response.url),
                    method=req.method.upper(),
                )
                if response.status_code == 429:
                    if attempt >= self._retry.max_attempts:
                        raise RateLimitError(
                            "Marketplace rate limit exceeded",
                            code="MARKETPLACE_RATE_LIMITED",
                            details=[{"field": "url", "issue": req.url}],
                        )
                    delay = self._compute_delay(attempt, response.headers.get("Retry-After"))
                    logger.warning(
                        "marketplace_rate_limited",
                        url=req.url,
                        attempt=attempt,
                        delay=delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                if response.status_code in self._retry.retry_statuses and attempt < self._retry.max_attempts:
                    delay = self._compute_delay(attempt, response.headers.get("Retry-After"))
                    await asyncio.sleep(delay)
                    continue
                return http_resp
            except (httpx.TimeoutException, httpx.NetworkError, httpx.TransportError) as exc:
                last_exc = exc
                if attempt >= self._retry.max_attempts:
                    break
                delay = self._compute_delay(attempt, None)
                logger.warning(
                    "marketplace_http_retry",
                    url=req.url,
                    attempt=attempt,
                    error=str(exc),
                    delay=delay,
                )
                await asyncio.sleep(delay)
        raise DependencyError(
            f"Marketplace HTTP request failed after retries: {last_exc}",
            code="MARKETPLACE_HTTP_FAILED",
            retryable=True,
            cause=last_exc,
        )

    def _compute_delay(self, attempt: int, retry_after: str | None) -> float:
        if retry_after:
            try:
                return min(float(retry_after), self._retry.max_delay_seconds)
            except ValueError:
                pass
        expo = self._retry.base_delay_seconds * (2 ** (attempt - 1))
        jitter = random.uniform(0, 0.25 * expo)
        return min(expo + jitter, self._retry.max_delay_seconds)


def translate_http_error(channel: str, resp: HttpResponse) -> MarketplaceError:
    """Map HTTP failures to MarketplaceError."""
    code = "MARKETPLACE_API_ERROR"
    retryable = resp.status_code >= 500 or resp.status_code == 429
    if resp.status_code == 401:
        code = "MARKETPLACE_UNAUTHORIZED"
        retryable = False
    elif resp.status_code == 403:
        code = "MARKETPLACE_FORBIDDEN"
        retryable = False
    elif resp.status_code == 429:
        code = "MARKETPLACE_RATE_LIMITED"
        retryable = True
    message = f"{channel} API error HTTP {resp.status_code}"
    if isinstance(resp.json_data, dict):
        message = str(resp.json_data.get("message") or resp.json_data.get("error") or message)
    return MarketplaceError(
        message,
        code=code,
        provider=channel,
        provider_code=str(resp.status_code),
        retryable=retryable,
        details=[{"field": "path", "issue": resp.url}],
    )
