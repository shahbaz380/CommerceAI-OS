"""Inventory domain enumerations."""

from __future__ import annotations

from enum import StrEnum


class InventoryItemStatus(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    SYNCING = "syncing"
    SYNCED = "synced"
    FAILED = "failed"
    ARCHIVED = "archived"


class InventorySyncStatus(StrEnum):
    NEVER = "never"
    PENDING = "pending"
    SYNCED = "synced"
    ERROR = "error"
    DELETED_REMOTE = "deleted_remote"


class InventoryCondition(StrEnum):
    NEW = "NEW"
    LIKE_NEW = "LIKE_NEW"
    NEW_OTHER = "NEW_OTHER"
    NEW_WITH_DEFECTS = "NEW_WITH_DEFECTS"
    MANUFACTURER_REFURBISHED = "MANUFACTURER_REFURBISHED"
    CERTIFIED_REFURBISHED = "CERTIFIED_REFURBISHED"
    EXCELLENT_REFURBISHED = "EXCELLENT_REFURBISHED"
    VERY_GOOD_REFURBISHED = "VERY_GOOD_REFURBISHED"
    GOOD_REFURBISHED = "GOOD_REFURBISHED"
    SELLER_REFURBISHED = "SELLER_REFURBISHED"
    USED_EXCELLENT = "USED_EXCELLENT"
    USED_VERY_GOOD = "USED_VERY_GOOD"
    USED_GOOD = "USED_GOOD"
    USED_ACCEPTABLE = "USED_ACCEPTABLE"
    FOR_PARTS_OR_NOT_WORKING = "FOR_PARTS_OR_NOT_WORKING"


INVENTORY_TRANSITIONS: dict[InventoryItemStatus, set[InventoryItemStatus]] = {
    InventoryItemStatus.DRAFT: {InventoryItemStatus.READY, InventoryItemStatus.ARCHIVED},
    InventoryItemStatus.READY: {
        InventoryItemStatus.SYNCING,
        InventoryItemStatus.DRAFT,
        InventoryItemStatus.ARCHIVED,
    },
    InventoryItemStatus.SYNCING: {
        InventoryItemStatus.SYNCED,
        InventoryItemStatus.FAILED,
    },
    InventoryItemStatus.SYNCED: {
        InventoryItemStatus.SYNCING,
        InventoryItemStatus.READY,
        InventoryItemStatus.ARCHIVED,
    },
    InventoryItemStatus.FAILED: {
        InventoryItemStatus.SYNCING,
        InventoryItemStatus.READY,
        InventoryItemStatus.DRAFT,
        InventoryItemStatus.ARCHIVED,
    },
    InventoryItemStatus.ARCHIVED: set(),
}
