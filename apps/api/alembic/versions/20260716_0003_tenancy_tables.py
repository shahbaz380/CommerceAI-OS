"""Multi-tenant organization/workspace tables.

Revision ID: 20260716_0003
Revises: 20260716_0002
Create Date: 2026-07-16
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.infrastructure.database.types.guid import GUID

revision: str = "20260716_0003"
down_revision: str | None = "20260716_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("status", sa.String(32), server_default="active", nullable=False),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("website", sa.String(300), nullable=True),
        sa.Column("timezone", sa.String(64), server_default="UTC", nullable=False),
        sa.Column("currency", sa.String(8), server_default="USD", nullable=False),
        sa.Column("language", sa.String(16), server_default="en", nullable=False),
        sa.Column("owner_user_id", GUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("preferences", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=True)
    op.create_index("ix_organizations_owner_user_id", "organizations", ["owner_user_id"])

    op.create_table(
        "workspaces",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("organization_id", GUID(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("status", sa.String(32), server_default="active", nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("timezone", sa.String(64), nullable=True),
        sa.Column("currency", sa.String(8), nullable=True),
        sa.Column("language", sa.String(16), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("is_default", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.UniqueConstraint("organization_id", "slug", name="uq_workspace_org_slug"),
    )
    op.create_index("ix_workspaces_organization_id", "workspaces", ["organization_id"])
    op.create_index("ix_workspaces_slug", "workspaces", ["slug"])

    op.create_table(
        "workspace_memberships",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("workspace_id", GUID(), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", GUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role_code", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), server_default="active", nullable=False),
        sa.Column("invited_by", GUID(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.UniqueConstraint("workspace_id", "user_id", name="uq_workspace_member"),
    )
    op.create_index("ix_workspace_memberships_workspace_id", "workspace_memberships", ["workspace_id"])
    op.create_index("ix_workspace_memberships_user_id", "workspace_memberships", ["user_id"])
    op.create_index("ix_workspace_memberships_role_code", "workspace_memberships", ["role_code"])

    op.create_table(
        "workspace_invitations",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("workspace_id", GUID(), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("role_code", sa.String(64), nullable=False),
        sa.Column("token_hash", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), server_default="pending", nullable=False),
        sa.Column("invited_by", GUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_by_user_id", GUID(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_workspace_invitations_workspace_id", "workspace_invitations", ["workspace_id"])
    op.create_index("ix_workspace_invitations_email", "workspace_invitations", ["email"])
    op.create_index("ix_workspace_invitations_token_hash", "workspace_invitations", ["token_hash"], unique=True)

    op.create_table(
        "user_profiles",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("user_id", GUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("display_name", sa.String(200), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("phone", sa.String(40), nullable=True),
        sa.Column("job_title", sa.String(120), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("timezone", sa.String(64), server_default="UTC", nullable=False),
        sa.Column("language", sa.String(16), server_default="en", nullable=False),
        sa.Column("theme", sa.String(16), server_default="system", nullable=False),
        sa.Column("notification_preferences", sa.JSON(), nullable=True),
        sa.Column("ui_preferences", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_user_profiles_user_id", "user_profiles", ["user_id"], unique=True)

    op.create_table(
        "organization_settings",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("organization_id", GUID(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("general", sa.JSON(), nullable=True),
        sa.Column("security", sa.JSON(), nullable=True),
        sa.Column("notifications", sa.JSON(), nullable=True),
        sa.Column("branding", sa.JSON(), nullable=True),
        sa.Column("regional", sa.JSON(), nullable=True),
        sa.Column("business_rules", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_organization_settings_organization_id", "organization_settings", ["organization_id"], unique=True)

    op.create_table(
        "workspace_settings",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("workspace_id", GUID(), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("preferences", sa.JSON(), nullable=True),
        sa.Column("marketplace", sa.JSON(), nullable=True),
        sa.Column("automation", sa.JSON(), nullable=True),
        sa.Column("ai", sa.JSON(), nullable=True),
        sa.Column("notifications", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_workspace_settings_workspace_id", "workspace_settings", ["workspace_id"], unique=True)

    op.create_table(
        "tenant_audit_events",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("organization_id", GUID(), nullable=True),
        sa.Column("workspace_id", GUID(), nullable=True),
        sa.Column("actor_user_id", GUID(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_tenant_audit_events_organization_id", "tenant_audit_events", ["organization_id"])
    op.create_index("ix_tenant_audit_events_workspace_id", "tenant_audit_events", ["workspace_id"])
    op.create_index("ix_tenant_audit_events_event_type", "tenant_audit_events", ["event_type"])


def downgrade() -> None:
    for t in (
        "tenant_audit_events",
        "workspace_settings",
        "organization_settings",
        "user_profiles",
        "workspace_invitations",
        "workspace_memberships",
        "workspaces",
        "organizations",
    ):
        op.drop_table(t)
