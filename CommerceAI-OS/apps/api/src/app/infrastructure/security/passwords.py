"""Argon2 password hashing via passlib."""

from __future__ import annotations

from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class PasswordHasher:
    def hash(self, password: str) -> str:
        return _pwd_context.hash(password)

    def verify(self, plain: str, hashed: str) -> bool:
        try:
            return _pwd_context.verify(plain, hashed)
        except Exception:
            return False

    def needs_rehash(self, hashed: str) -> bool:
        return _pwd_context.needs_update(hashed)


_hasher: PasswordHasher | None = None


def get_password_hasher() -> PasswordHasher:
    global _hasher
    if _hasher is None:
        _hasher = PasswordHasher()
    return _hasher
