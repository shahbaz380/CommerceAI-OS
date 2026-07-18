"""Authentication application service."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import AppSettings, get_settings
from app.domain.identity.policies import (
    validate_email_format,
    validate_password_strength,
    validate_username,
)
from app.domain.identity.roles import RoleCode
from app.infrastructure.logging.setup import get_logger
from app.infrastructure.persistence.models.identity import (
    LoginHistoryModel,
    RefreshTokenModel,
    SecurityEventModel,
    UserModel,
    UserRoleModel,
    UserSessionModel,
)
from app.infrastructure.persistence.repositories.identity import (
    AuditRepository,
    RefreshTokenRepository,
    RoleRepository,
    SessionRepository,
    UserRepository,
)
from app.infrastructure.security.jwt import JWTService, TokenPair
from app.infrastructure.security.passwords import PasswordHasher, get_password_hasher
from app.infrastructure.security.tokens import hash_token, new_session_token
from app.shared.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    ValidationAppError,
)

logger = get_logger("app.security")


@dataclass(slots=True)
class AuthResult:
    user: UserModel
    tokens: TokenPair
    session_id: uuid.UUID


class AuthService:
    """Register, login, logout, refresh, session management."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        settings: AppSettings | None = None,
        jwt: JWTService | None = None,
        hasher: PasswordHasher | None = None,
    ) -> None:
        self.session = session
        self.settings = settings or get_settings()
        self.jwt = jwt or JWTService(self.settings)
        self.hasher = hasher or get_password_hasher()
        self.users = UserRepository(session)
        self.roles = RoleRepository(session)
        self.sessions = SessionRepository(session)
        self.refresh_tokens = RefreshTokenRepository(session)
        self.audit = AuditRepository(session)

    async def register(
        self,
        *,
        email: str,
        password: str,
        full_name: str | None = None,
        username: str | None = None,
        role_code: str = RoleCode.ORGANIZATION_OWNER.value,
    ) -> UserModel:
        email = validate_email_format(email)
        password = validate_password_strength(password)
        username = validate_username(username)

        if await self.users.get_by_email(email):
            raise ConflictError("Email already registered", code="EMAIL_TAKEN")
        if username and await self.users.get_by_username(username):
            raise ConflictError("Username already taken", code="USERNAME_TAKEN")

        user = UserModel(
            email=email,
            username=username,
            password_hash=self.hasher.hash(password),
            full_name=full_name,
            password_changed_at=datetime.now(UTC),
            is_active=True,
            is_superuser=False,
        )
        await self.users.add(user)

        role = await self.roles.get_by_code(role_code)
        if role is None:
            # catalog may not be seeded yet
            raise ValidationAppError(
                f"Role '{role_code}' not found; seed identity catalog first",
                details=[{"field": "role", "issue": "missing"}],
            )
        self.session.add(UserRoleModel(user_id=user.id, role_id=role.id))
        await self.session.flush()

        await self.audit.add_security_event(
            SecurityEventModel(
                user_id=user.id,
                event_type="user.registered",
                severity="info",
                message=f"User registered: {email}",
                metadata_json={"role": role_code},
            )
        )
        # reload with roles
        reloaded = await self.users.get_by_id(user.id)
        assert reloaded is not None
        logger.info("user_registered", user_id=str(user.id))
        return reloaded

    async def login(
        self,
        *,
        email: str,
        password: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        remember_me: bool = False,
        device_name: str | None = None,
    ) -> AuthResult:
        email = validate_email_format(email)
        user = await self.users.get_by_email(email)

        async def fail(reason: str, uid: uuid.UUID | None = None) -> None:
            await self.audit.add_login(
                LoginHistoryModel(
                    user_id=uid,
                    email_attempted=email,
                    success=False,
                    failure_reason=reason,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
            )
            await self.session.flush()

        if user is None:
            await fail("user_not_found")
            raise AuthenticationError("Invalid email or password", code="INVALID_CREDENTIALS")

        if user.locked_until and user.locked_until > datetime.now(UTC):
            await fail("account_locked", user.id)
            raise AuthenticationError("Account is temporarily locked", code="ACCOUNT_LOCKED")

        if not user.is_active:
            await fail("inactive", user.id)
            raise AuthenticationError("Account is inactive", code="ACCOUNT_INACTIVE")

        if not self.hasher.verify(password, user.password_hash):
            user.failed_login_count += 1
            max_attempts = 5
            if user.failed_login_count >= max_attempts:
                user.locked_until = datetime.now(UTC) + timedelta(minutes=15)
                await self.audit.add_security_event(
                    SecurityEventModel(
                        user_id=user.id,
                        event_type="auth.account_locked",
                        severity="warning",
                        message="Account locked after failed logins",
                        ip_address=ip_address,
                        metadata_json={"failed_login_count": user.failed_login_count},
                    )
                )
            await fail("bad_password", user.id)
            raise AuthenticationError("Invalid email or password", code="INVALID_CREDENTIALS")

        # success
        user.failed_login_count = 0
        user.locked_until = None
        user.last_login_at = datetime.now(UTC)
        if self.hasher.needs_rehash(user.password_hash):
            user.password_hash = self.hasher.hash(password)

        roles, permissions = await self._roles_and_permissions(user)
        session_token = new_session_token()
        session_days = 30 if remember_me else max(self.settings.refresh_token_expire_days, 1)
        session = UserSessionModel(
            user_id=user.id,
            session_token_hash=hash_token(session_token),
            device_name=device_name,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=datetime.now(UTC) + timedelta(days=session_days),
            last_seen_at=datetime.now(UTC),
            remember_me=remember_me,
        )
        await self.sessions.add(session)

        pair = self.jwt.issue_pair(
            subject=str(user.id),
            roles=roles,
            permissions=permissions,
            session_id=str(session.id),
            is_superuser=user.is_superuser,
            remember_me=remember_me,
        )
        session.refresh_jti = pair.refresh_jti

        await self.refresh_tokens.add(
            RefreshTokenModel(
                user_id=user.id,
                jti=pair.refresh_jti,
                token_hash=hash_token(pair.refresh_token),
                session_id=session.id,
                expires_at=datetime.now(UTC)
                + timedelta(days=self.settings.refresh_token_expire_days * (2 if remember_me else 1)),
                ip_address=ip_address,
                user_agent=user_agent,
            )
        )

        await self.audit.add_login(
            LoginHistoryModel(
                user_id=user.id,
                email_attempted=email,
                success=True,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        )
        await self.audit.add_security_event(
            SecurityEventModel(
                user_id=user.id,
                event_type="auth.login",
                severity="info",
                message="User logged in",
                ip_address=ip_address,
                metadata_json={"session_id": str(session.id), "remember_me": remember_me},
            )
        )
        await self.session.flush()
        logger.info("user_login", user_id=str(user.id), session_id=str(session.id))
        return AuthResult(user=user, tokens=pair, session_id=session.id)

    async def refresh(
        self,
        *,
        refresh_token: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuthResult:
        payload = self.jwt.decode(refresh_token, expected_type="refresh")
        stored = await self.refresh_tokens.get_by_jti(payload.jti)
        if stored is None or stored.revoked_at is not None:
            raise AuthenticationError("Refresh token revoked or unknown", code="REFRESH_REVOKED")
        exp = stored.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=UTC)
        if exp < datetime.now(UTC):
            raise AuthenticationError("Refresh token expired", code="REFRESH_EXPIRED")
        if stored.token_hash != hash_token(refresh_token):
            # possible theft — revoke family
            await self.refresh_tokens.revoke_all_for_user(stored.user_id)
            await self.audit.add_security_event(
                SecurityEventModel(
                    user_id=stored.user_id,
                    event_type="auth.refresh_reuse",
                    severity="critical",
                    message="Refresh token hash mismatch — revoked all tokens",
                    ip_address=ip_address,
                )
            )
            await self.session.flush()
            raise AuthenticationError("Refresh token reuse detected", code="REFRESH_REUSE")

        user = await self.users.get_by_id(uuid.UUID(payload.sub))
        if user is None or not user.is_active:
            raise AuthenticationError("User not found or inactive", code="USER_INACTIVE")

        roles, permissions = await self._roles_and_permissions(user)
        session_id = payload.sid
        pair = self.jwt.issue_pair(
            subject=str(user.id),
            roles=roles,
            permissions=permissions,
            session_id=session_id,
            is_superuser=user.is_superuser,
        )
        await self.refresh_tokens.revoke(stored, replaced_by=pair.refresh_jti)
        await self.refresh_tokens.add(
            RefreshTokenModel(
                user_id=user.id,
                jti=pair.refresh_jti,
                token_hash=hash_token(pair.refresh_token),
                session_id=uuid.UUID(session_id) if session_id else stored.session_id,
                expires_at=datetime.now(UTC) + timedelta(days=self.settings.refresh_token_expire_days),
                ip_address=ip_address,
                user_agent=user_agent,
            )
        )
        if session_id:
            sess = await self.sessions.get_by_id(uuid.UUID(session_id))
            if sess and sess.revoked_at is None:
                sess.last_seen_at = datetime.now(UTC)
                sess.refresh_jti = pair.refresh_jti
        await self.session.flush()
        sid = uuid.UUID(session_id) if session_id else (stored.session_id or uuid.uuid4())
        return AuthResult(user=user, tokens=pair, session_id=sid)

    async def logout(
        self,
        *,
        user_id: uuid.UUID,
        refresh_token: str | None = None,
        session_id: uuid.UUID | None = None,
        all_devices: bool = False,
        ip_address: str | None = None,
    ) -> None:
        if all_devices:
            await self.sessions.revoke_all_for_user(user_id)
            await self.refresh_tokens.revoke_all_for_user(user_id)
        else:
            if refresh_token:
                try:
                    payload = self.jwt.decode(refresh_token, expected_type="refresh")
                    stored = await self.refresh_tokens.get_by_jti(payload.jti)
                    if stored:
                        await self.refresh_tokens.revoke(stored)
                    if payload.sid:
                        sess = await self.sessions.get_by_id(uuid.UUID(payload.sid))
                        if sess:
                            await self.sessions.revoke(sess)
                except AuthenticationError:
                    pass
            if session_id:
                sess = await self.sessions.get_by_id(session_id)
                if sess and sess.user_id == user_id:
                    await self.sessions.revoke(sess)
        await self.audit.add_security_event(
            SecurityEventModel(
                user_id=user_id,
                event_type="auth.logout",
                severity="info",
                message="User logged out",
                ip_address=ip_address,
                metadata_json={"all_devices": all_devices},
            )
        )
        await self.session.flush()

    async def change_password(
        self,
        *,
        user_id: uuid.UUID,
        current_password: str,
        new_password: str,
        ip_address: str | None = None,
    ) -> None:
        user = await self.users.get_by_id(user_id)
        if user is None:
            raise AuthenticationError("User not found", code="USER_NOT_FOUND")
        if not self.hasher.verify(current_password, user.password_hash):
            raise AuthenticationError("Current password is incorrect", code="BAD_PASSWORD")
        new_password = validate_password_strength(new_password)
        user.password_hash = self.hasher.hash(new_password)
        user.password_changed_at = datetime.now(UTC)
        await self.sessions.revoke_all_for_user(user_id)
        await self.refresh_tokens.revoke_all_for_user(user_id)
        await self.audit.add_security_event(
            SecurityEventModel(
                user_id=user_id,
                event_type="auth.password_changed",
                severity="info",
                message="Password changed; sessions revoked",
                ip_address=ip_address,
            )
        )
        await self.session.flush()

    async def request_password_reset(self, email: str) -> dict[str, Any]:
        """Placeholder — does not send email; returns generic response."""
        email = validate_email_format(email)
        user = await self.users.get_by_email(email)
        if user:
            await self.audit.add_security_event(
                SecurityEventModel(
                    user_id=user.id,
                    event_type="auth.password_reset_requested",
                    severity="info",
                    message="Password reset requested (email delivery not configured)",
                )
            )
            await self.session.flush()
        return {
            "message": "If the account exists, password reset instructions will be sent",
            "email_delivery": "not_configured",
        }

    async def request_email_verification(self, user_id: uuid.UUID) -> dict[str, Any]:
        """Placeholder — marks intent only."""
        user = await self.users.get_by_id(user_id)
        if user is None:
            raise AuthorizationError("User not found", code="USER_NOT_FOUND")
        await self.audit.add_security_event(
            SecurityEventModel(
                user_id=user_id,
                event_type="auth.email_verification_requested",
                severity="info",
                message="Email verification requested (delivery not configured)",
            )
        )
        await self.session.flush()
        return {"message": "Verification email queued", "email_delivery": "not_configured"}

    async def list_sessions(self, user_id: uuid.UUID) -> list[UserSessionModel]:
        return await self.sessions.list_active_for_user(user_id)

    async def revoke_session(self, user_id: uuid.UUID, session_id: uuid.UUID) -> None:
        sess = await self.sessions.get_by_id(session_id)
        if sess is None or sess.user_id != user_id:
            raise AuthorizationError("Session not found", code="SESSION_NOT_FOUND")
        await self.sessions.revoke(sess)
        await self.session.flush()

    async def _roles_and_permissions(self, user: UserModel) -> tuple[list[str], list[str]]:
        # Ensure roles loaded
        if not user.roles:
            reloaded = await self.users.get_by_id(user.id)
            user = reloaded or user
        roles: list[str] = []
        permissions: set[str] = set()
        for ur in user.roles or []:
            role = ur.role
            if role is None:
                continue
            roles.append(role.code)
            # load permissions if needed
            full = await self.roles.get_by_code(role.code)
            if full and full.permissions:
                for rp in full.permissions:
                    if rp.permission:
                        permissions.add(rp.permission.code)
        if user.is_superuser and RoleCode.SUPER_ADMIN.value not in roles:
            roles.append(RoleCode.SUPER_ADMIN.value)
        return roles, sorted(permissions)
