"""SKU value object and validation."""

from __future__ import annotations

import re

from app.shared.exceptions import ValidationAppError

_SKU_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._\-]{0,63}$")
_RESERVED = {"null", "undefined", "none", "n/a", "na", "test", "sample"}


def normalize_sku(sku: str) -> str:
    cleaned = sku.strip().upper()
    cleaned = re.sub(r"\s+", "-", cleaned)
    return cleaned


def validate_sku(sku: str, *, prefix: str | None = None) -> str:
    if not sku or not str(sku).strip():
        raise ValidationAppError(
            "SKU is required",
            details=[{"field": "sku", "issue": "required"}],
        )
    value = normalize_sku(sku)
    if prefix:
        p = normalize_sku(prefix)
        if not value.startswith(p):
            value = f"{p}{value}" if p.endswith("-") else f"{p}-{value}"
    if not _SKU_RE.match(value):
        raise ValidationAppError(
            "Invalid SKU format",
            details=[{"field": "sku", "issue": "format"}],
        )
    if value.lower() in _RESERVED:
        raise ValidationAppError(
            "SKU is reserved",
            details=[{"field": "sku", "issue": "reserved"}],
        )
    return value


def auto_generate_sku(*, prefix: str = "SKU", seed: str) -> str:
    base = re.sub(r"[^A-Za-z0-9]", "", seed.upper())[:12] or "ITEM"
    return validate_sku(f"{prefix}-{base}")
