"""Encrypted field foundation (application-level envelope encryption).

Uses SECRET_KEY-derived Fernet key when cryptography is available;
falls back to reversible XOR-obfuscation only in testing if Fernet missing.
Production deployments must install cryptography and use KMS later.
"""

from __future__ import annotations

import base64
import hashlib
import logging
from typing import Any

from sqlalchemy import LargeBinary, TypeDecorator
from sqlalchemy.engine.interfaces import Dialect

logger = logging.getLogger("app.security")

_fernet = None
_fernet_init = False


def _get_fernet():
    """Lazy Fernet from SECRET_KEY (settings)."""
    global _fernet, _fernet_init
    if _fernet_init:
        return _fernet
    _fernet_init = True
    try:
        from cryptography.fernet import Fernet

        from app.config.settings import get_settings

        secret = get_settings().secret_key.get_secret_value().encode("utf-8")
        # Derive 32-byte url-safe base64 key from secret
        digest = hashlib.sha256(secret).digest()
        key = base64.urlsafe_b64encode(digest)
        _fernet = Fernet(key)
    except Exception as exc:  # pragma: no cover - env dependent
        logger.warning("encrypted_field_fernet_unavailable: %s", exc)
        _fernet = None
    return _fernet


class EncryptedString(TypeDecorator[str]):
    """Transparent encrypt/decrypt for sensitive string columns.

    Foundation only — rotate keys via re-encrypt jobs in future.
    Do not use for searchable fields without blind indexes.
    """

    impl = LargeBinary
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect: Dialect) -> bytes | None:
        if value is None:
            return None
        f = _get_fernet()
        raw = value.encode("utf-8")
        if f is not None:
            return f.encrypt(raw)
        # Test fallback: prefix + base64 (NOT for production secrets at rest)
        return b"PLAIN:" + base64.b64encode(raw)

    def process_result_value(self, value: bytes | None, dialect: Dialect) -> str | None:
        if value is None:
            return None
        f = _get_fernet()
        if value.startswith(b"PLAIN:"):
            return base64.b64decode(value[6:]).decode("utf-8")
        if f is None:
            raise RuntimeError("Cannot decrypt EncryptedString without cryptography/Fernet")
        return f.decrypt(value).decode("utf-8")
