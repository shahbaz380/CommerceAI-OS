"""Marketplace integration foundation tables.

Revision ID: 20260716_0004
Revises: 20260716_0003
Create Date: 2026-07-16
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.infrastructure.database.types.guid import GUID

revision: str = "20260716_0004"
down_revision: str | None = "20260716_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "marketplace_connections",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("channel", sa.String(32), nullable=False),
        sa.Column("environment", sa.String(16), server_default="sandbox", nullable=False),
        sa.Column("status", sa.String(32), server_default="pending", nullable=False),
        sa.Column("display_name", sa.String(200), nullable=True),
        sa.Column("external_account_id", sa.String(128), nullable=True),
        sa.Column("external_username", sa.String(200), nullable=True),
        sa.Column("scopes", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_code", sa.String(64), nullable=True),
        sa.Column("last_error_message", sa.Text(), nullable=True),
        sa.Column("connected_by_user_id", GUID(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("connected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disconnected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.UniqueConstraint(
            "workspace_id", "channel", "external_account_id", name="uq_marketplace_connection_external"
        ),
    )
    op.create_index("ix_marketplace_connections_workspace_id", "marketplace_connections", ["workspace_id"])
    op.create_index("ix_marketplace_connections_channel", "marketplace_connections", ["channel"])
    op.create_index("ix_marketplace_connections_status", "marketplace_connections", ["status"])
    op.create_index(
        "ix_marketplace_connections_external_account_id", "marketplace_connections", ["external_account_id"]
    )

    # Encrypted columns stored as LargeBinary by EncryptedString TypeDecorator
    op.create_table(
        "marketplace_oauth_tokens",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column(
            "connection_id",
            GUID(),
            sa.ForeignKey("marketplace_connections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("access_token_encrypted", sa.LargeBinary(), nullable=False),
        sa.Column("refresh_token_encrypted", sa.LargeBinary(), nullable=True),
        sa.Column("token_type", sa.String(32), server_default="Bearer", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refresh_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scope", sa.Text(), nullable=True),
        sa.Column("is_current", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rotation_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_marketplace_oauth_tokens_connection_id", "marketplace_oauth_tokens", ["connection_id"])

    op.create_table(
        "marketplace_credentials",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("channel", sa.String(32), nullable=False),
        sa.Column("environment", sa.String(16), nullable=False),
        sa.Column("client_id", sa.String(255), nullable=False),
        sa.Column("client_secret_encrypted", sa.LargeBinary(), nullable=False),
        sa.Column("redirect_uri", sa.String(500), nullable=False),
        sa.Column("scopes", sa.Text(), nullable=True),
        sa.Column("ru_name", sa.String(200), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("label", sa.String(120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "workspace_id", "channel", "environment", name="uq_marketplace_credentials_ws_channel_env"
        ),
    )
    op.create_index("ix_marketplace_credentials_workspace_id", "marketplace_credentials", ["workspace_id"])
    op.create_index("ix_marketplace_credentials_channel", "marketplace_credentials", ["channel"])

    op.create_table(
        "marketplace_oauth_states",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("state", sa.String(128), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("channel", sa.String(32), nullable=False),
        sa.Column("environment", sa.String(16), nullable=False),
        sa.Column("user_id", GUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("redirect_uri", sa.String(500), nullable=False),
        sa.Column("code_verifier", sa.String(128), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_marketplace_oauth_states_state", "marketplace_oauth_states", ["state"], unique=True)
    op.create_index("ix_marketplace_oauth_states_workspace_id", "marketplace_oauth_states", ["workspace_id"])

    op.create_table(
        "marketplace_token_refresh_history",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column(
            "connection_id",
            GUID(),
            sa.ForeignKey("marketplace_connections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index(
        "ix_marketplace_token_refresh_history_connection_id",
        "marketplace_token_refresh_history",
        ["connection_id"],
    )

    op.create_table(
        "marketplace_sync_history",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column(
            "connection_id",
            GUID(),
            sa.ForeignKey("marketplace_connections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stats", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_marketplace_sync_history_connection_id", "marketplace_sync_history", ["connection_id"])
    op.create_index("ix_marketplace_sync_history_workspace_id", "marketplace_sync_history", ["workspace_id"])

    op.create_table(
        "marketplace_api_logs",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("connection_id", GUID(), nullable=True),
        sa.Column("workspace_id", GUID(), nullable=True),
        sa.Column("channel", sa.String(32), nullable=False),
        sa.Column("method", sa.String(16), nullable=False),
        sa.Column("path", sa.String(500), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("rate_limited", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_marketplace_api_logs_channel", "marketplace_api_logs", ["channel"])
    op.create_index("ix_marketplace_api_logs_connection_id", "marketplace_api_logs", ["connection_id"])
    op.create_index("ix_marketplace_api_logs_workspace_id", "marketplace_api_logs", ["workspace_id"])

    op.create_table(
        "marketplace_webhook_events",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("channel", sa.String(32), nullable=False),
        sa.Column("event_type", sa.String(128), nullable=True),
        sa.Column("signature_valid", sa.Boolean(), nullable=True),
        sa.Column("headers", sa.JSON(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("processed", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("process_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_marketplace_webhook_events_channel", "marketplace_webhook_events", ["channel"])


def downgrade() -> None:
    for t in (
        "marketplace_webhook_events",
        "marketplace_api_logs",
        "marketplace_sync_history",
        "marketplace_token_refresh_history",
        "marketplace_oauth_states",
        "marketplace_credentials",
        "marketplace_oauth_tokens",
        "marketplace_connections",
    ):
        op.drop_table(t)
