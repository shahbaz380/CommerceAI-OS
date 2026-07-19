"""JWT access/refresh token service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from app.config.settings import AppSettings, get_settings
from app.infrastructure.security.tokens import new_jti
from app.shared.exceptions import AuthenticationError


@dataclass(slots=True, frozen=True)
class TokenPayload:
    sub: str
    type: str
    jti: str
    exp: datetime
    iat: datetime
    sid: str | None = None
    roles: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()
    is_superuser: bool = False


@dataclass(slots=True, frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 0
    refresh_jti: str = ""
    access_jti: str = ""
    session_id: str | None = None


class JWTService:
    def __init__(self, settings: AppSettings | None = None) -> None:
        self.settings = settings or get_settings()
        self._secret = self.settings.secret_key.get_secret_value()
        self._alg = self.settings.jwt_algorithm

    def create_access_token(
        self,
        *,
        subject: str,
        roles: list[str] | None = None,
        permissions: list[str] | None = None,
        session_id: str | None = None,
        is_superuser: bool = False,
        extra: dict[str, Any] | None = None,
    ) -> tuple[str, str, datetime]:
        jti = new_jti()
        now = datetime.now(UTC)
        exp = now + timedelta(minutes=self.settings.access_token_expire_minutes)
        payload: dict[str, Any] = {
            "sub": subject,
            "type": "access",
            "jti": jti,
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
            "roles": roles or [],
            "permissions": permissions or [],
            "is_superuser": is_superuser,
        }
        if session_id:
            payload["sid"] = session_id
        if extra:
            payload.update(extra)
        token = jwt.encode(payload, self._secret, algorithm=self._alg)
        return token, jti, exp

    def create_refresh_token(
        self,
        *,
        subject: str,
        session_id: str | None = None,
        remember_me: bool = False,
    ) -> tuple[str, str, datetime]:
        jti = new_jti()
        now = datetime.now(UTC)
        days = self.settings.refresh_token_expire_days
        if remember_me:
            days = max(days, 30)
        exp = now + timedelta(days=days)
        payload: dict[str, Any] = {
            "sub": subject,
            "type": "refresh",
            "jti": jti,
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }
        if session_id:
            payload["sid"] = session_id
        token = jwt.encode(payload, self._secret, algorithm=self._alg)
        return token, jti, exp

    def decode(self, token: str, *, expected_type: str | None = None) -> TokenPayload:
        try:
            data = jwt.decode(token, self._secret, algorithms=[self._alg])
        except JWTError as exc:
            raise AuthenticationError("Invalid or expired token", code="INVALID_TOKEN") from exc

        token_type = str(data.get("type", ""))
        if expected_type and token_type != expected_type:
            raise AuthenticationError("Unexpected token type", code="INVALID_TOKEN_TYPE")

        exp_ts = data.get("exp")
        iat_ts = data.get("iat")
        if exp_ts is None or iat_ts is None or "sub" not in data or "jti" not in data:
            raise AuthenticationError("Malformed token", code="MALFORMED_TOKEN")

        return TokenPayload(
            sub=str(data["sub"]),
            type=token_type,
            jti=str(data["jti"]),
            exp=datetime.fromtimestamp(int(exp_ts), tz=UTC),
            iat=datetime.fromtimestamp(int(iat_ts), tz=UTC),
            sid=str(data["sid"]) if data.get("sid") else None,
            roles=tuple(data.get("roles") or ()),
            permissions=tuple(data.get("permissions") or ()),
            is_superuser=bool(data.get("is_superuser", False)),
        )

    def issue_pair(
        self,
        *,
        subject: str,
        roles: list[str],
        permissions: list[str],
        session_id: str | None = None,
        is_superuser: bool = False,
        remember_me: bool = False,
    ) -> TokenPair:
        access, access_jti, access_exp = self.create_access_token(
            subject=subject,
            roles=roles,
            permissions=permissions,
            session_id=session_id,
            is_superuser=is_superuser,
        )
        refresh, refresh_jti, _ = self.create_refresh_token(
            subject=subject,
            session_id=session_id,
            remember_me=remember_me,
        )
        expires_in = int((access_exp - datetime.now(UTC)).total_seconds())
        return TokenPair(
            access_token=access,
            refresh_token=refresh,
            expires_in=max(expires_in, 0),
            refresh_jti=refresh_jti,
            access_jti=access_jti,
            session_id=session_id,
        )
