"""Tenancy API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    slug: str | None = Field(default=None, max_length=100)
    timezone: str = "UTC"
    currency: str = Field(default="USD", max_length=8)
    language: str = Field(default="en", max_length=16)
    default_workspace_name: str = "Default"


class OrganizationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    logo_url: str | None = None
    website: str | None = None
    timezone: str | None = None
    currency: str | None = None
    language: str | None = None
    status: str | None = None
    preferences: dict[str, Any] | None = None


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    status: str
    logo_url: str | None = None
    website: str | None = None
    timezone: str
    currency: str
    language: str
    owner_user_id: UUID
    preferences: dict[str, Any] | None = None
    created_at: datetime


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    slug: str | None = None
    description: str | None = None
    timezone: str | None = None
    currency: str | None = None
    language: str | None = None


class WorkspaceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    timezone: str | None = None
    currency: str | None = None
    language: str | None = None
    status: str | None = None
    metadata_json: dict[str, Any] | None = None


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    name: str
    slug: str
    status: str
    description: str | None = None
    timezone: str | None = None
    currency: str | None = None
    language: str | None = None
    is_default: bool
    metadata_json: dict[str, Any] | None = Field(default=None, validation_alias="metadata_json")
    created_at: datetime


class InviteCreate(BaseModel):
    email: EmailStr
    role_code: str = "staff"
    message: str | None = None
    expires_days: int = Field(default=7, ge=1, le=30)


class InviteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    email: str
    role_code: str
    status: str
    expires_at: datetime
    created_at: datetime
    # raw token only on create
    token: str | None = None


class InviteTokenRequest(BaseModel):
    token: str


class MembershipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    user_id: UUID
    role_code: str
    status: str
    joined_at: datetime | None = None


class MembershipRoleUpdate(BaseModel):
    role_code: str


class TransferOwnershipRequest(BaseModel):
    new_owner_user_id: UUID


class ProfileUpdate(BaseModel):
    display_name: str | None = None
    avatar_url: str | None = None
    phone: str | None = None
    job_title: str | None = None
    bio: str | None = None
    timezone: str | None = None
    language: str | None = None
    theme: str | None = None
    notification_preferences: dict[str, Any] | None = None
    ui_preferences: dict[str, Any] | None = None


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    display_name: str | None = None
    avatar_url: str | None = None
    phone: str | None = None
    job_title: str | None = None
    bio: str | None = None
    timezone: str
    language: str
    theme: str
    notification_preferences: dict[str, Any] | None = None
    ui_preferences: dict[str, Any] | None = None


class OrgSettingsUpdate(BaseModel):
    general: dict[str, Any] | None = None
    security: dict[str, Any] | None = None
    notifications: dict[str, Any] | None = None
    branding: dict[str, Any] | None = None
    regional: dict[str, Any] | None = None
    business_rules: dict[str, Any] | None = None


class OrgSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    organization_id: UUID
    general: dict[str, Any] | None = None
    security: dict[str, Any] | None = None
    notifications: dict[str, Any] | None = None
    branding: dict[str, Any] | None = None
    regional: dict[str, Any] | None = None
    business_rules: dict[str, Any] | None = None


class WorkspaceSettingsUpdate(BaseModel):
    preferences: dict[str, Any] | None = None
    marketplace: dict[str, Any] | None = None
    automation: dict[str, Any] | None = None
    ai: dict[str, Any] | None = None
    notifications: dict[str, Any] | None = None


class WorkspaceSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    workspace_id: UUID
    preferences: dict[str, Any] | None = None
    marketplace: dict[str, Any] | None = None
    automation: dict[str, Any] | None = None
    ai: dict[str, Any] | None = None
    notifications: dict[str, Any] | None = None


class TenantContextResponse(BaseModel):
    organization_id: UUID | None = None
    workspace_id: UUID | None = None
    role_code: str | None = None
    membership_status: str | None = None
