"""Marketplace integration ORM models — connections, tokens, logs (no listings/orders)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.infrastructure.database.base import Base, SoftDeleteModel, TimestampedModel
from app.infrastructure.database.mixins.tenant import TenantOwnedMixin
from app.infrastructure.database.mixins.version import VersionMixin
from app.infrastructure.database.types.encrypted import EncryptedString
from app.infrastructure.database.types.guid import GUID

JSONType = JSON().with_variant(JSONB(), "postgresql")


class MarketplaceConnectionModel(SoftDeleteModel, TenantOwnedMixin, VersionMixin):
    """Workspace-linked marketplace account connection."""

    __tablename__ = "marketplace_connections"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "channel",
            "external_account_id",
            name="uq_marketplace_connection_external",
        ),
    )
    __mapper_args__ = {"version_id_col": VersionMixin.version}

    channel: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    environment: Mapped[str] = mapped_column(
        String(16), default="sandbox", server_default="sandbox", nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), default="pending", server_default="pending", nullable=False, index=True
    )
    display_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    external_account_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    external_username: Mapped[str | None] = mapped_column(String(200), nullable=True)
    scopes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONType, nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    connected_by_user_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("users.id"), nullable=True)
    connected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    disconnected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    alias: Mapped[str | None] = mapped_column(String(120), nullable=True)
    region: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_refreshed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    suspended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MarketplaceOAuthTokenModel(TimestampedModel):
    """Encrypted OAuth token set for a connection (versioned history allowed)."""

    __tablename__ = "marketplace_oauth_tokens"

    connection_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("marketplace_connections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    access_token_encrypted: Mapped[str] = mapped_column(EncryptedString(), nullable=False)
    refresh_token_encrypted: Mapped[str | None] = mapped_column(EncryptedString(), nullable=True)
    token_type: Mapped[str] = mapped_column(String(32), default="Bearer", server_default="Bearer", nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    refresh_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scope: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rotation_version: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)


class MarketplaceCredentialModel(SoftDeleteModel, TenantOwnedMixin):
    """Developer app credentials (client id/secret) per workspace/channel/env."""

    __tablename__ = "marketplace_credentials"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "channel",
            "environment",
            name="uq_marketplace_credentials_ws_channel_env",
        ),
    )

    channel: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    environment: Mapped[str] = mapped_column(String(16), nullable=False)
    client_id: Mapped[str] = mapped_column(String(255), nullable=False)
    client_secret_encrypted: Mapped[str] = mapped_column(EncryptedString(), nullable=False)
    redirect_uri: Mapped[str] = mapped_column(String(500), nullable=False)
    scopes: Mapped[str | None] = mapped_column(Text, nullable=True)
    ru_name: Mapped[str | None] = mapped_column(String(200), nullable=True)  # eBay RuName
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    label: Mapped[str | None] = mapped_column(String(120), nullable=True)


class MarketplaceOAuthStateModel(Base):
    """CSRF/state store for OAuth authorization callbacks."""

    __tablename__ = "marketplace_oauth_states"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    state: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    environment: Mapped[str] = mapped_column(String(16), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)
    redirect_uri: Mapped[str] = mapped_column(String(500), nullable=False)
    code_verifier: Mapped[str | None] = mapped_column(String(128), nullable=True)
    nonce: Mapped[str | None] = mapped_column(String(128), nullable=True)
    connection_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MarketplaceTokenRefreshHistoryModel(Base):
    __tablename__ = "marketplace_token_refresh_history"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    connection_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("marketplace_connections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MarketplaceSyncHistoryModel(Base):
    """Foundation sync job history (entity_type free-form; no business sync yet)."""

    __tablename__ = "marketplace_sync_history"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    connection_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("marketplace_connections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    stats_json: Mapped[dict[str, Any] | None] = mapped_column("stats", JSONType, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MarketplaceApiLogModel(Base):
    """API call log for monitoring (no response bodies with secrets)."""

    __tablename__ = "marketplace_api_logs"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    connection_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True, index=True)
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True, index=True)
    channel: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    method: Mapped[str] = mapped_column(String(16), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rate_limited: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MarketplaceWebhookEventModel(Base):
    """Inbound webhook envelope store (verification + dispatch foundation)."""

    __tablename__ = "marketplace_webhook_events"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    channel: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    event_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    signature_valid: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    headers_json: Mapped[dict[str, Any] | None] = mapped_column("headers", JSONType, nullable=True)
    payload_json: Mapped[dict[str, Any] | None] = mapped_column("payload", JSONType, nullable=True)
    processed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    process_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
