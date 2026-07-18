"""Authentication / authorization FastAPI dependencies."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.identity.auth_service import AuthService
from app.application.identity.authorization import AuthorizationService, Principal
from app.config.settings import get_settings
from app.infrastructure.persistence.repositories.identity import SessionRepository, UserRepository
from app.infrastructure.security.jwt import JWTService
from app.presentation.api.deps.common import get_db_session
from app.shared.exceptions import AuthenticationError

http_bearer = HTTPBearer(auto_error=False)
_authz = AuthorizationService()


async def get_auth_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AuthService:
    return AuthService(session, settings=get_settings(), jwt=JWTService(get_settings()))


async def get_current_principal(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(http_bearer)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Principal:
    if credentials is None or not credentials.credentials:
        raise AuthenticationError("Not authenticated", code="NOT_AUTHENTICATED")

    token = credentials.credentials
    jwt_svc = JWTService(get_settings())
    payload = jwt_svc.decode(token, expected_type="access")

    try:
        user_id = uuid.UUID(payload.sub)
    except ValueError as exc:
        raise AuthenticationError("Invalid subject", code="INVALID_TOKEN") from exc

    if payload.sid:
        try:
            sid = uuid.UUID(payload.sid)
            sess = await SessionRepository(session).get_by_id(sid)
            if sess is None or sess.revoked_at is not None:
                raise AuthenticationError("Session revoked", code="SESSION_REVOKED")
            expires = sess.expires_at
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=UTC)
            if expires < datetime.now(UTC):
                raise AuthenticationError("Session expired", code="SESSION_EXPIRED")
        except AuthenticationError:
            raise

    user = await UserRepository(session).get_by_id(user_id)
    if user is None or not user.is_active:
        raise AuthenticationError("User inactive or missing", code="USER_INACTIVE")

    principal = Principal(
        user_id=user_id,
        email=user.email,
        roles=list(payload.roles),
        permissions=list(payload.permissions),
        is_superuser=payload.is_superuser or user.is_superuser,
        session_id=uuid.UUID(payload.sid) if payload.sid else None,
        token_jti=payload.jti,
    )
    request.state.principal = principal
    return principal


async def get_optional_principal(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(http_bearer)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Principal | None:
    if credentials is None or not credentials.credentials:
        return None
    try:
        return await get_current_principal(request, credentials, session)
    except AuthenticationError:
        return None


def require_permissions(*permissions: str) -> Callable:
    async def _dep(principal: Annotated[Principal, Depends(get_current_principal)]) -> Principal:
        return _authz.require_any_permission(principal, *permissions)

    return _dep


def require_permission(permission: str) -> Callable:
    async def _dep(principal: Annotated[Principal, Depends(get_current_principal)]) -> Principal:
        return _authz.require_permission(principal, permission)

    return _dep


def require_superuser() -> Callable:
    async def _dep(principal: Annotated[Principal, Depends(get_current_principal)]) -> Principal:
        return _authz.require_superuser(principal)

    return _dep
