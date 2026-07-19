"""Listing domain exceptions."""

from __future__ import annotations

from app.shared.exceptions import AppError, BusinessRuleError, NotFoundError


class ListingNotFoundError(NotFoundError):
    def __init__(self, message: str = "Listing not found") -> None:
        super().__init__(message, code="LISTING_NOT_FOUND")


class InvalidListingStatusTransitionError(BusinessRuleError):
    def __init__(self, current: str, target: str) -> None:
        super().__init__(
            f"Invalid listing status transition: {current} → {target}",
            code="INVALID_LISTING_STATUS_TRANSITION",
            details=[{"field": "status", "issue": f"{current}->{target}"}],
        )


class ListingValidationError(BusinessRuleError):
    def __init__(self, message: str = "Listing validation failed", *, details: list | None = None) -> None:
        super().__init__(message, code="LISTING_VALIDATION_FAILED", details=details or [])


class ListingApprovalError(BusinessRuleError):
    def __init__(self, message: str = "Listing cannot be approved") -> None:
        super().__init__(message, code="LISTING_APPROVAL_ERROR")


class ListingScheduleError(BusinessRuleError):
    def __init__(self, message: str = "Invalid listing schedule") -> None:
        super().__init__(message, code="LISTING_SCHEDULE_ERROR")


class ListingTenantMismatchError(AppError):
    code = "LISTING_TENANT_MISMATCH"
    http_status = 403

    def __init__(self, message: str = "Listing does not belong to this workspace") -> None:
        super().__init__(message, code=self.code)


class ListingTemplateNotFoundError(NotFoundError):
    def __init__(self, message: str = "Listing template not found") -> None:
        super().__init__(message, code="LISTING_TEMPLATE_NOT_FOUND")


class MarketplaceConnectionMismatchError(AppError):
    code = "MARKETPLACE_CONNECTION_MISMATCH"
    http_status = 400

    def __init__(self, message: str = "Marketplace connection mismatch") -> None:
        super().__init__(message, code=self.code)
