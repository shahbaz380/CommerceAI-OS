"""Inventory status transitions."""

from __future__ import annotations

from app.domain.inventory.enums import INVENTORY_TRANSITIONS, InventoryItemStatus
from app.domain.inventory.exceptions import InvalidInventoryStatusTransitionError


def assert_inventory_transition(
    current: str | InventoryItemStatus,
    target: str | InventoryItemStatus,
) -> InventoryItemStatus:
    cur = InventoryItemStatus(current)
    tgt = InventoryItemStatus(target)
    if tgt == cur:
        return cur
    allowed = INVENTORY_TRANSITIONS.get(cur, set())
    if tgt not in allowed:
        raise InvalidInventoryStatusTransitionError(cur.value, tgt.value)
    return tgt
