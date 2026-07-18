"""Authentication HTTP routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.identity.auth_service import AuthService
from app.application.identity.authorization import Principal
from app.application.identity.bootstrap import seed_identity_catalog
from app.presentation.api.deps.auth import get_auth_service, get_current_principal
from app.presentation.api.deps.common import get_db_session
from app.presentation.schemas.identity.auth import (
    AuthTokenResponse,
    ChangePasswordRequest,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    PasswordResetRequest,
    RefreshRequest,
    RegisterRequest,
    SessionResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_meta(request: Request) -> tuple[str | None, str | None]:
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return ip, ua


def _user_response(user, roles: list[str], permissions: list[str]) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        email_verified_at=user.email_verified_at,
        last_login_at=user.last_login_at,
        roles=roles,
        permissions=permissions,
    )


@router.post("/register", response_model=AuthTokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthTokenResponse:
    # Ensure RBAC catalog exists
    await seed_identity_catalog(session)
    user = await auth.register(
        email=str(body.email),
        password=body.password,
        full_name=body.full_name,
        username=body.username,
    )
    ip, ua = _client_meta(request)
    result = await auth.login(
        email=user.email,
        password=body.password,
        ip_address=ip,
        user_agent=ua,
    )
    roles, permissions = await auth._roles_and_permissions(result.user)
    return AuthTokenResponse(
        access_token=result.tokens.access_token,
        refresh_token=result.tokens.refresh_token,
        expires_in=result.tokens.expires_in,
        session_id=result.session_id,
        user=_user_response(result.user, roles, permissions),
    )


@router.post("/login", response_model=AuthTokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthTokenResponse:
    await seed_identity_catalog(session)
    ip, ua = _client_meta(request)
    result = await auth.login(
        email=str(body.email),
        password=body.password,
        ip_address=ip,
        user_agent=ua,
        remember_me=body.remember_me,
        device_name=body.device_name,
    )
    roles, permissions = await auth._roles_and_permissions(result.user)
    return AuthTokenResponse(
        access_token=result.tokens.access_token,
        refresh_token=result.tokens.refresh_token,
        expires_in=result.tokens.expires_in,
        session_id=result.session_id,
        user=_user_response(result.user, roles, permissions),
    )


@router.post("/refresh", response_model=AuthTokenResponse)
async def refresh(
    body: RefreshRequest,
    request: Request,
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthTokenResponse:
    ip, ua = _client_meta(request)
    result = await auth.refresh(refresh_token=body.refresh_token, ip_address=ip, user_agent=ua)
    roles, permissions = await auth._roles_and_permissions(result.user)
    return AuthTokenResponse(
        access_token=result.tokens.access_token,
        refresh_token=result.tokens.refresh_token,
        expires_in=result.tokens.expires_in,
        session_id=result.session_id,
        user=_user_response(result.user, roles, permissions),
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    body: LogoutRequest,
    request: Request,
    principal: Annotated[Principal, Depends(get_current_principal)],
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> MessageResponse:
    ip, _ = _client_meta(request)
    await auth.logout(
        user_id=principal.user_id,
        refresh_token=body.refresh_token,
        session_id=principal.session_id,
        all_devices=body.all_devices,
        ip_address=ip,
    )
    return MessageResponse(message="Logged out")


@router.get("/me", response_model=UserResponse)
async def me(
    principal: Annotated[Principal, Depends(get_current_principal)],
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    user = await auth.users.get_by_id(principal.user_id)
    assert user is not None
    return _user_response(user, principal.roles, principal.permissions)


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    body: ChangePasswordRequest,
    request: Request,
    principal: Annotated[Principal, Depends(get_current_principal)],
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> MessageResponse:
    ip, _ = _client_meta(request)
    await auth.change_password(
        user_id=principal.user_id,
        current_password=body.current_password,
        new_password=body.new_password,
        ip_address=ip,
    )
    return MessageResponse(message="Password changed; please login again")


@router.post("/password-reset/request", response_model=MessageResponse)
async def password_reset_request(
    body: PasswordResetRequest,
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> MessageResponse:
    result = await auth.request_password_reset(str(body.email))
    return MessageResponse(message=result["message"], details=result)


@router.post("/email-verification/request", response_model=MessageResponse)
async def email_verification_request(
    principal: Annotated[Principal, Depends(get_current_principal)],
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> MessageResponse:
    result = await auth.request_email_verification(principal.user_id)
    return MessageResponse(message=result["message"], details=result)


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(
    principal: Annotated[Principal, Depends(get_current_principal)],
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> list[SessionResponse]:
    sessions = await auth.list_sessions(principal.user_id)
    return [SessionResponse.model_validate(s) for s in sessions]


@router.delete("/sessions/{session_id}", response_model=MessageResponse)
async def revoke_session(
    session_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> MessageResponse:
    await auth.revoke_session(principal.user_id, session_id)
    return MessageResponse(message="Session revoked")
