"""Marketplace API Gateway interface + base implementation helpers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.infrastructure.marketplace.http.client import AsyncHttpClient, HttpRequest, HttpResponse


@dataclass(slots=True)
class GatewayRequest:
    method: str
    path: str
    headers: dict[str, str] = field(default_factory=dict)
    params: dict[str, Any] | None = None
    json_body: dict[str, Any] | None = None
    data: dict[str, Any] | str | None = None
    auth_bearer: str | None = None
    timeout: float | None = None


@dataclass(slots=True)
class GatewayResponse:
    status_code: int
    data: Any
    headers: dict[str, str]
    duration_ms: int
    raw_text: str


class MarketplaceGateway(ABC):
    """Gateway Pattern: channel-specific API surface over HTTP client."""

    channel: str

    @abstractmethod
    async def execute(self, request: GatewayRequest) -> GatewayResponse:
        raise NotImplementedError

    @abstractmethod
    async def health(self) -> dict[str, Any]:
        raise NotImplementedError


class BaseMarketplaceGateway(MarketplaceGateway):
    def __init__(self, *, base_url: str, http: AsyncHttpClient, channel: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.http = http
        self.channel = channel

    def build_url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.base_url}{path}"

    def build_headers(self, request: GatewayRequest) -> dict[str, str]:
        headers = {"Accept": "application/json", **request.headers}
        if request.auth_bearer:
            headers["Authorization"] = f"Bearer {request.auth_bearer}"
        return headers

    async def execute(self, request: GatewayRequest) -> GatewayResponse:
        http_req = HttpRequest(
            method=request.method,
            url=self.build_url(request.path),
            headers=self.build_headers(request),
            params=request.params,
            json_body=request.json_body,
            data=request.data,
            timeout=request.timeout,
        )
        resp: HttpResponse = await self.http.request(http_req)
        return GatewayResponse(
            status_code=resp.status_code,
            data=resp.json_data if resp.json_data is not None else resp.text,
            headers=resp.headers,
            duration_ms=resp.duration_ms,
            raw_text=resp.text,
        )

    async def health(self) -> dict[str, Any]:
        return {
            "channel": self.channel,
            "base_url": self.base_url,
            "status": "configured",
        }
