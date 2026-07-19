"""Product catalog enumerations."""

from __future__ import annotations

from enum import StrEnum


class ProductStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class ProductCondition(StrEnum):
    NEW = "new"
    LIKE_NEW = "like_new"
    VERY_GOOD = "very_good"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    FOR_PARTS = "for_parts"
    REFURBISHED = "refurbished"
    USED = "used"
    OTHER = "other"


class IdentifierType(StrEnum):
    SKU = "sku"
    UPC = "upc"
    EAN = "ean"
    ISBN = "isbn"
    GTIN = "gtin"
    MPN = "mpn"


class AttributeDataType(StrEnum):
    TEXT = "text"
    INTEGER = "integer"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    ENUM = "enum"
    MULTI_SELECT = "multi_select"
    JSON = "json"


class MediaStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    FAILED = "failed"
    ARCHIVED = "archived"


class CategoryStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


# Valid product status transitions
PRODUCT_TRANSITIONS: dict[ProductStatus, set[ProductStatus]] = {
    ProductStatus.DRAFT: {ProductStatus.ACTIVE, ProductStatus.ARCHIVED},
    ProductStatus.ACTIVE: {ProductStatus.INACTIVE, ProductStatus.ARCHIVED},
    ProductStatus.INACTIVE: {ProductStatus.ACTIVE, ProductStatus.ARCHIVED},
    ProductStatus.ARCHIVED: set(),
}
