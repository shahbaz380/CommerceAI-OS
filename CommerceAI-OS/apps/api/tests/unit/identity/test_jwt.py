"""JWT service tests."""

from app.config.settings import AppSettings
from app.infrastructure.security.jwt import JWTService
from app.shared.exceptions import AuthenticationError
import pytest


def test_access_roundtrip() -> None:
    settings = AppSettings(
        SECRET_KEY="unit-test-secret-key-with-32-bytes-minimum!",
        APP_ENV="testing",
    )
    svc = JWTService(settings)
    token, jti, exp = svc.create_access_token(
        subject="11111111-1111-1111-1111-111111111111",
        roles=["staff"],
        permissions=["order.read"],
    )
    payload = svc.decode(token, expected_type="access")
    assert payload.jti == jti
    assert payload.roles == ("staff",)
    assert "order.read" in payload.permissions


def test_wrong_type() -> None:
    settings = AppSettings(
        SECRET_KEY="unit-test-secret-key-with-32-bytes-minimum!",
        APP_ENV="testing",
    )
    svc = JWTService(settings)
    token, _, _ = svc.create_refresh_token(subject="11111111-1111-1111-1111-111111111111")
    with pytest.raises(AuthenticationError):
        svc.decode(token, expected_type="access")
