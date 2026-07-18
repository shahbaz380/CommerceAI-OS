"""Password policy tests."""

import pytest

from app.domain.identity.policies import validate_password_strength
from app.shared.exceptions import ValidationAppError


def test_password_ok() -> None:
    assert validate_password_strength("Str0ng!Passw0rd") == "Str0ng!Passw0rd"


def test_password_too_short() -> None:
    with pytest.raises(ValidationAppError):
        validate_password_strength("Short1!")


def test_password_missing_special() -> None:
    with pytest.raises(ValidationAppError):
        validate_password_strength("NoSpecialChar12")
