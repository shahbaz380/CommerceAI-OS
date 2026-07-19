"""Listing validation framework — no external marketplace API calls."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.domain.listings.enums import ValidationSeverity


@dataclass(slots=True)
class ListingValidationIssue:
    severity: str
    code: str
    message: str
    field: str | None = None


@dataclass(slots=True)
class ListingValidationResult:
    passed: bool
    validator_name: str
    issues: list[ListingValidationIssue] = field(default_factory=list)
    summary: str | None = None

    @property
    def errors(self) -> list[ListingValidationIssue]:
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]

    @property
    def warnings(self) -> list[ListingValidationIssue]:
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]


class ListingValidator(ABC):
    name: str = "base"

    @abstractmethod
    def validate(self, listing_data: dict[str, Any], content: dict[str, Any] | None = None) -> ListingValidationResult:
        raise NotImplementedError


class DefaultListingValidator(ListingValidator):
    """Core marketplace-independent listing completeness rules."""

    name = "default"

    def __init__(
        self,
        *,
        max_title_length: int = 80,
        min_description_length: int = 1,
        require_category_for_approval: bool = True,
    ) -> None:
        self.max_title_length = max_title_length
        self.min_description_length = min_description_length
        self.require_category_for_approval = require_category_for_approval

    def validate(self, listing_data: dict[str, Any], content: dict[str, Any] | None = None) -> ListingValidationResult:
        issues: list[ListingValidationIssue] = []
        title = (listing_data.get("marketplace_title") or listing_data.get("internal_title") or "").strip()
        if not title:
            issues.append(
                ListingValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="TITLE_REQUIRED",
                    field="title",
                    message="Listing title is required",
                )
            )
        elif len(title) > self.max_title_length:
            issues.append(
                ListingValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="TITLE_TOO_LONG",
                    field="title",
                    message=f"Title exceeds {self.max_title_length} characters",
                )
            )

        description = ((content or {}).get("description") or "").strip()
        if len(description) < self.min_description_length:
            issues.append(
                ListingValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="DESCRIPTION_REQUIRED",
                    field="description",
                    message="Listing description is required",
                )
            )

        price = listing_data.get("price_amount")
        if price is not None:
            try:
                if float(price) < 0:
                    issues.append(
                        ListingValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            code="PRICE_NEGATIVE",
                            field="price_amount",
                            message="Price cannot be negative",
                        )
                    )
            except (TypeError, ValueError):
                issues.append(
                    ListingValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        code="PRICE_INVALID",
                        field="price_amount",
                        message="Price is invalid",
                    )
                )

        qty = listing_data.get("quantity")
        if qty is not None and int(qty) < 0:
            issues.append(
                ListingValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="QUANTITY_NEGATIVE",
                    field="quantity",
                    message="Quantity cannot be negative",
                )
            )

        currency = (listing_data.get("currency") or "").strip().upper()
        if currency and len(currency) != 3:
            issues.append(
                ListingValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="CURRENCY_INVALID",
                    field="currency",
                    message="Currency must be a 3-letter code",
                )
            )

        if self.require_category_for_approval and not listing_data.get("category_id"):
            issues.append(
                ListingValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code="CATEGORY_MISSING",
                    field="category_id",
                    message="Category is recommended before approval",
                )
            )

        if not listing_data.get("listing_format"):
            issues.append(
                ListingValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="FORMAT_REQUIRED",
                    field="listing_format",
                    message="Listing format is required",
                )
            )

        errors = [i for i in issues if i.severity == ValidationSeverity.ERROR]
        return ListingValidationResult(
            passed=len(errors) == 0,
            validator_name=self.name,
            issues=issues,
            summary="OK" if not errors else f"{len(errors)} blocking issue(s)",
        )


class ValidationRegistry:
    def __init__(self) -> None:
        self._validators: dict[str, ListingValidator] = {"default": DefaultListingValidator()}

    def register(self, key: str, validator: ListingValidator) -> None:
        self._validators[key] = validator

    def get(self, key: str = "default") -> ListingValidator:
        return self._validators.get(key) or self._validators["default"]

    def validate_all(
        self, listing_data: dict[str, Any], content: dict[str, Any] | None = None, *, keys: list[str] | None = None
    ) -> ListingValidationResult:
        selected = keys or list(self._validators.keys())
        merged: list[ListingValidationIssue] = []
        names: list[str] = []
        for key in selected:
            validator = self.get(key)
            result = validator.validate(listing_data, content)
            merged.extend(result.issues)
            names.append(validator.name)
        errors = [i for i in merged if i.severity == ValidationSeverity.ERROR]
        return ListingValidationResult(
            passed=len(errors) == 0,
            validator_name="+".join(names),
            issues=merged,
            summary="OK" if not errors else f"{len(errors)} blocking issue(s)",
        )
