"""Organization / workspace multi-tenant ORM models (no commerce tables)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.infrastructure.database.base import Base, SoftDeleteModel, TimestampedModel
from app.infrastructure.database.mixins.version import VersionMixin
from app.infrastructure.database.types.guid import GUID

JSONType = JSON().with_variant(JSONB(), "postgresql")


class OrganizationModel(SoftDeleteModel, VersionMixin):
    """Top-level company / tenant account."""

    __tablename__ = "organizations"
    __mapper_args__ = {"version_id_col": VersionMixin.version}

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="active", server_default="active", nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    website: Mapped[str | None] = mapped_column(String(300), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", server_default="UTC", nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="USD", server_default="USD", nullable=False)
    language: Mapped[str] = mapped_column(String(16), default="en", server_default="en", nullable=False)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    preferences: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)

    workspaces: Mapped[list[WorkspaceModel]] = relationship(back_populates="organization")
    settings: Mapped[OrganizationSettingsModel | None] = relationship(
        back_populates="organization",
        uselist=False,
    )


class WorkspaceModel(SoftDeleteModel, VersionMixin):
    """Primary operational tenant boundary (workspace_id on commerce data later)."""

    __tablename__ = "workspaces"
    __table_args__ = (UniqueConstraint("organization_id", "slug", name="uq_workspace_org_slug"),)
    __mapper_args__ = {"version_id_col": VersionMixin.version}

    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="active", server_default="active", nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONType, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)

    organization: Mapped[OrganizationModel] = relationship(back_populates="workspaces")
    memberships: Mapped[list[WorkspaceMembershipModel]] = relationship(back_populates="workspace")
    settings: Mapped[WorkspaceSettingsModel | None] = relationship(
        back_populates="workspace",
        uselist=False,
    )


class WorkspaceMembershipModel(TimestampedModel):
    __tablename__ = "workspace_memberships"
    __table_args__ = (UniqueConstraint("workspace_id", "user_id", name="uq_workspace_member"),)

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="active", server_default="active", nullable=False)
    invited_by: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("users.id"), nullable=True)
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    workspace: Mapped[WorkspaceModel] = relationship(back_populates="memberships")


class WorkspaceInvitationModel(TimestampedModel):
    __tablename__ = "workspace_invitations"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    role_code: Mapped[str] = mapped_column(String(64), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", server_default="pending", nullable=False)
    invited_by: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    accepted_by_user_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("users.id"), nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)


class UserProfileModel(TimestampedModel):
    """Extended profile for a global user (1:1)."""

    __tablename__ = "user_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    display_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    job_title: Mapped[str | None] = mapped_column(String(120), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", server_default="UTC", nullable=False)
    language: Mapped[str] = mapped_column(String(16), default="en", server_default="en", nullable=False)
    theme: Mapped[str] = mapped_column(String(16), default="system", server_default="system", nullable=False)
    notification_preferences: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    ui_preferences: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)


class OrganizationSettingsModel(TimestampedModel):
    __tablename__ = "organization_settings"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    general: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    security: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    notifications: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    branding: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    regional: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    business_rules: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)

    organization: Mapped[OrganizationModel] = relationship(back_populates="settings")


class WorkspaceSettingsModel(TimestampedModel):
    __tablename__ = "workspace_settings"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    preferences: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    marketplace: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    automation: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    ai: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    notifications: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)

    workspace: Mapped[WorkspaceModel] = relationship(back_populates="settings")


class TenantAuditModel(Base):
    """Tenant-scoped audit trail for org/workspace lifecycle events."""

    __tablename__ = "tenant_audit_events"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True, index=True)
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True, index=True)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("users.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
