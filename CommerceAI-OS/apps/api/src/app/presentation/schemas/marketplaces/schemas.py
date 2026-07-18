"""Marketplace API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class MarketplaceChannelInfo(BaseModel):
    channel: str
    status: str | None = None
    capabilities: list[str] | None = None
    business_apis: bool | None = None


class CredentialCreate(BaseModel):
    channel: str = "ebay"
    environment: str = Field(default="sandbox", pattern="^(sandbox|production)$")
    client_id: str = Field(min_length=1, max_length=255)
    client_secret: str = Field(min_length=1)
    redirect_uri: str = Field(min_length=1, max_length=500)
    scopes: str | None = None
    ru_name: str | None = None
    label: str | None = None


class CredentialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    channel: str
    environment: str
    client_id: str
    redirect_uri: str
    scopes: str | None = None
    ru_name: str | None = None
    label: str | None = None
    is_active: bool
    # never expose secret


class ConnectStartRequest(BaseModel):
    channel: str = "ebay"
    environment: str = Field(default="sandbox", pattern="^(sandbox|production)$")
    display_name: str | None = None


class ConnectStartResponse(BaseModel):
    connection_id: UUID
    status: str
    authorization_url: str | None = None
    state: str | None = None
    channel: str
    environment: str


class ConnectCallbackRequest(BaseModel):
    channel: str = "ebay"
    code: str
    state: str
    connection_id: UUID | None = None


class ConnectCallbackResponse(BaseModel):
    connection_id: UUID
    status: str
    external_account_id: str | None = None
    display_name: str | None = None


class ConnectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    channel: str
    environment: str
    status: str
    display_name: str | None = None
    external_account_id: str | None = None
    external_username: str | None = None
    scopes: str | None = None
    last_success_at: datetime | None = None
    last_error_code: str | None = None
    last_error_message: str | None = None
    connected_at: datetime | None = None
    disconnected_at: datetime | None = None
    created_at: datetime


class ConnectionHealthResponse(BaseModel):
    connection_id: str
    channel: str
    status: str
    environment: str
    last_success_at: str | None = None
    last_error_code: str | None = None
    validation: dict[str, Any]
    healthy: bool


class WebhookReceiveResponse(BaseModel):
    id: UUID
    channel: str
    processed: bool
    signature_valid: bool | None = None
