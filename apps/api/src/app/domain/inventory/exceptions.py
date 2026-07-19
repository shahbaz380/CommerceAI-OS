"""Inventory domain exceptions."""

from __future__ import annotations

from app.shared.exceptions import AppError, BusinessRuleError, ConflictError, NotFoundError


class InventoryNotFoundError(NotFoundError):
    def __init__(self, message: str = "Inventory item not found") -> None:
        super().__init__(message, code="INVENTORY_NOT_FOUND")


class InventoryValidationError(BusinessRuleError):
    def __init__(self, message: str = "Inventory validation failed", *, details: list | None = None) -> None:
        super().__init__(message, code="INVENTORY_VALIDATION_ERROR", details=details or [])


class InventorySyncFailedError(AppError):
    code = "INVENTORY_SYNC_FAILED"
    http_status = 502
    retryable = True

    def __init__(self, message: str = "Inventory sync failed", *, cause: Exception | None = None) -> None:
        super().__init__(message, code=self.code, retryable=True, cause=cause)


class DuplicateInventorySKUError(ConflictError):
    def __init__(self, sku: str) -> None:
        super().__init__(
            f"Inventory SKU already exists: {sku}",
            code="DUPLICATE_INVENTORY_SKU",
            details=[{"field": "sku", "issue": sku}],
        )


class InventoryAlreadySyncedError(ConflictError):
    def __init__(self, message: str = "Inventory item already synced") -> None:
        super().__init__(message, code="INVENTORY_ALREADY_SYNCED")


class InventoryArchivedError(BusinessRuleError):
    def __init__(self, message: str = "Inventory item is archived") -> None:
        super().__init__(message, code="INVENTORY_ARCHIVED")


class MarketplaceConnectionRequiredError(BusinessRuleError):
    def __init__(self, message: str = "Connected marketplace account is required") -> None:
        super().__init__(message, code="MARKETPLACE_CONNECTION_REQUIRED")


class InvalidInventoryStatusTransitionError(BusinessRuleError):
    def __init__(self, current: str, target: str) -> None:
        super().__init__(
            f"Invalid inventory status transition: {current} → {target}",
            code="INVALID_INVENTORY_STATUS_TRANSITION",
            details=[{"field": "status", "issue": f"{current}->{target}"}],
        )
