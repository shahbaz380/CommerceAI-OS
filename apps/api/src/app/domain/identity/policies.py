"""Password and identity security policies."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.shared.exceptions import ValidationAppError


@dataclass(frozen=True, slots=True)
class PasswordPolicy:
    min_length: int = 12
    require_upper: bool = True
    require_lower: bool = True
    require_digit: bool = True
    require_special: bool = True
    max_length: int = 128


DEFAULT_PASSWORD_POLICY = PasswordPolicy()

_SPECIAL = re.compile(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?`~]")


def validate_password_strength(
    password: str,
    *,
    policy: PasswordPolicy = DEFAULT_PASSWORD_POLICY,
) -> str:
    if len(password) < policy.min_length:
        raise ValidationAppError(
            f"Password must be at least {policy.min_length} characters",
            details=[{"field": "password", "issue": "too_short"}],
        )
    if len(password) > policy.max_length:
        raise ValidationAppError(
            f"Password must be at most {policy.max_length} characters",
            details=[{"field": "password", "issue": "too_long"}],
        )
    if policy.require_upper and not any(c.isupper() for c in password):
        raise ValidationAppError(
            "Password must contain an uppercase letter",
            details=[{"field": "password", "issue": "missing_upper"}],
        )
    if policy.require_lower and not any(c.islower() for c in password):
        raise ValidationAppError(
            "Password must contain a lowercase letter",
            details=[{"field": "password", "issue": "missing_lower"}],
        )
    if policy.require_digit and not any(c.isdigit() for c in password):
        raise ValidationAppError(
            "Password must contain a digit",
            details=[{"field": "password", "issue": "missing_digit"}],
        )
    if policy.require_special and not _SPECIAL.search(password):
        raise ValidationAppError(
            "Password must contain a special character",
            details=[{"field": "password", "issue": "missing_special"}],
        )
    return password


def validate_email_format(email: str) -> str:
    email = email.strip().lower()
    if "@" not in email or "." not in email.split("@")[-1]:
        raise ValidationAppError(
            "Invalid email address",
            details=[{"field": "email", "issue": "invalid"}],
        )
    if len(email) > 320:
        raise ValidationAppError(
            "Email too long",
            details=[{"field": "email", "issue": "too_long"}],
        )
    return email


def validate_username(username: str | None) -> str | None:
    if username is None:
        return None
    username = username.strip()
    if not username:
        return None
    if len(username) < 3 or len(username) > 64:
        raise ValidationAppError(
            "Username must be 3–64 characters",
            details=[{"field": "username", "issue": "length"}],
        )
    if not re.fullmatch(r"[a-zA-Z0-9_\.\-]+", username):
        raise ValidationAppError(
            "Username contains invalid characters",
            details=[{"field": "username", "issue": "charset"}],
        )
    return username
