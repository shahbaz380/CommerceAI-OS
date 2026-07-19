"""Common validation helpers used by schemas later."""

from __future__ import annotations


def non_empty_str(value: str, *, field_name: str = "value") -> str:
    cleaned = value.strip()
    if not cleaned:
        from app.shared.exceptions import ValidationAppError

        raise ValidationAppError(
            f"{field_name} must not be empty",
            details=[{"field": field_name, "issue": "empty"}],
        )
    return cleaned
