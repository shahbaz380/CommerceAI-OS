"""Catalog domain exceptions."""

from __future__ import annotations

from app.shared.exceptions import AppError, BusinessRuleError, ConflictError, NotFoundError


class ProductNotFoundError(NotFoundError):
    def __init__(self, message: str = "Product not found") -> None:
        super().__init__(message, code="PRODUCT_NOT_FOUND")


class ProductVariantNotFoundError(NotFoundError):
    def __init__(self, message: str = "Product variant not found") -> None:
        super().__init__(message, code="PRODUCT_VARIANT_NOT_FOUND")


class DuplicateSKUError(ConflictError):
    def __init__(self, sku: str) -> None:
        super().__init__(
            f"SKU already exists: {sku}",
            code="DUPLICATE_SKU",
            details=[{"field": "sku", "issue": sku}],
        )


class InvalidProductStatusTransitionError(BusinessRuleError):
    def __init__(self, current: str, target: str) -> None:
        super().__init__(
            f"Invalid product status transition: {current} → {target}",
            code="INVALID_PRODUCT_STATUS_TRANSITION",
            details=[{"field": "status", "issue": f"{current}->{target}"}],
        )


class InvalidProductIdentifierError(BusinessRuleError):
    def __init__(self, message: str = "Invalid product identifier") -> None:
        super().__init__(message, code="INVALID_PRODUCT_IDENTIFIER")


class ProductTenantMismatchError(AppError):
    code = "PRODUCT_TENANT_MISMATCH"
    http_status = 403

    def __init__(self, message: str = "Product does not belong to this workspace") -> None:
        super().__init__(message, code=self.code)


class CategoryNotFoundError(NotFoundError):
    def __init__(self, message: str = "Category not found") -> None:
        super().__init__(message, code="CATEGORY_NOT_FOUND")


class CategoryHierarchyError(BusinessRuleError):
    def __init__(self, message: str = "Invalid category hierarchy") -> None:
        super().__init__(message, code="CATEGORY_HIERARCHY_ERROR")


class DuplicatePrimaryImageError(ConflictError):
    def __init__(self) -> None:
        super().__init__("Primary image already exists for this scope", code="DUPLICATE_PRIMARY_IMAGE")


class MediaNotFoundError(NotFoundError):
    def __init__(self, message: str = "Media not found") -> None:
        super().__init__(message, code="MEDIA_NOT_FOUND")
