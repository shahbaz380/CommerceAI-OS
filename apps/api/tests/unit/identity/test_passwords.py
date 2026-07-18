"""Argon2 password hasher tests."""

from app.infrastructure.security.passwords import PasswordHasher


def test_hash_and_verify() -> None:
    h = PasswordHasher()
    hashed = h.hash("Str0ng!Passw0rd")
    assert hashed != "Str0ng!Passw0rd"
    assert h.verify("Str0ng!Passw0rd", hashed)
    assert not h.verify("wrong", hashed)
