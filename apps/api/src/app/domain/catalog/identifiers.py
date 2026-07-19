"""Product identifier format validation."""

from __future__ import annotations

import re

from app.domain.catalog.enums import IdentifierType
from app.domain.catalog.exceptions import InvalidProductIdentifierError
from app.domain.catalog.sku import validate_sku


def validate_identifier(identifier_type: str, value: str) -> str:
    raw = value.strip()
    if not raw:
        raise InvalidProductIdentifierError("Identifier value is required")
    itype = IdentifierType(identifier_type)
    if itype == IdentifierType.SKU:
        return validate_sku(raw)
    digits = re.sub(r"\D", "", raw)
    if itype == IdentifierType.UPC:
        if len(digits) not in (12, 11):
            raise InvalidProductIdentifierError("UPC must be 12 digits")
        return digits.zfill(12)
    if itype == IdentifierType.EAN:
        if len(digits) not in (13, 12, 8):
            raise InvalidProductIdentifierError("EAN must be 8 or 13 digits")
        return digits
    if itype == IdentifierType.GTIN:
        if len(digits) not in (8, 12, 13, 14):
            raise InvalidProductIdentifierError("GTIN must be 8, 12, 13, or 14 digits")
        return digits
    if itype == IdentifierType.ISBN:
        cleaned = raw.replace("-", "").replace(" ", "").upper()
        if len(cleaned) not in (10, 13):
            raise InvalidProductIdentifierError("ISBN must be 10 or 13 characters")
        return cleaned
    if itype == IdentifierType.MPN:
        if len(raw) > 64:
            raise InvalidProductIdentifierError("MPN too long")
        return raw
    return raw
