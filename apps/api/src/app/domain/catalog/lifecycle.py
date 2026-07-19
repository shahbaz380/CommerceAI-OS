"""Product status transition rules."""

from __future__ import annotations

from app.domain.catalog.enums import PRODUCT_TRANSITIONS, ProductStatus
from app.domain.catalog.exceptions import InvalidProductStatusTransitionError


def assert_product_transition(current: str | ProductStatus, target: str | ProductStatus) -> ProductStatus:
    cur = ProductStatus(current)
    tgt = ProductStatus(target)
    if tgt == cur:
        return cur
    allowed = PRODUCT_TRANSITIONS.get(cur, set())
    if tgt not in allowed:
        raise InvalidProductStatusTransitionError(cur.value, tgt.value)
    return tgt
