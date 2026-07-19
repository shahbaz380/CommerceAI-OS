"""Identity API schemas (Pydantic v2)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    full_name: str | None = Field(default=None, max_length=200)
    username: str | None = Field(default=None, min_length=3, max_length=64)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False
    device_name: str | None = Field(default=None, max_length=200)


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str | None = None
    all_devices: bool = False


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=12, max_length=128)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    username: str | None = None
    full_name: str | None = None
    is_active: bool
    is_superuser: bool
    email_verified_at: datetime | None = None
    last_login_at: datetime | None = None
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)


class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    session_id: UUID
    user: UserResponse


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    device_name: str | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime
    expires_at: datetime
    last_seen_at: datetime | None
    remember_me: bool


class MessageResponse(BaseModel):
    message: str
    details: dict | None = None


class RoleResponse(BaseModel):
    code: str
    name: str
    hierarchy_rank: int
    is_system: bool


class PermissionResponse(BaseModel):
    code: str
    module: str
    description: str | None = None
