"""Opaque token helpers (sessions, refresh storage)."""

from __future__ import annotations

import hashlib
import secrets
import uuid


def new_jti() -> str:
    return uuid.uuid4().hex


def new_session_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
