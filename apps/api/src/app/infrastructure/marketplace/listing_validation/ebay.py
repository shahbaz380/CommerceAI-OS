"""eBay listing policy placeholder validator — no external API calls."""

from __future__ import annotations

from typing import Any

from app.domain.listings.enums import ValidationSeverity
from app.infrastructure.marketplace.listing_validation.base import (
    ListingValidationIssue,
    ListingValidationResult,
    ListingValidator,
)


class EbayListingPolicyValidator(ListingValidator):
    """Basic eBay-oriented content policy checks (offline)."""

    name = "ebay_policy"

    # Common restricted patterns — illustrative foundation only
    _BLOCKED_TERMS = ("guaranteed ranking", "counterfeit", "replica watch")

    def validate(self, listing_data: dict[str, Any], content: dict[str, Any] | None = None) -> ListingValidationResult:
        issues: list[ListingValidationIssue] = []
        title = (listing_data.get("marketplace_title") or listing_data.get("internal_title") or "").lower()
        description = ((content or {}).get("description") or "").lower()
        blob = f"{title} {description}"
        for term in self._BLOCKED_TERMS:
            if term in blob:
                issues.append(
                    ListingValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        code="EBAY_POLICY_TERM",
                        field="content",
                        message=f"Content may violate policy term: '{term}'",
                    )
                )
        title_raw = listing_data.get("marketplace_title") or listing_data.get("internal_title") or ""
        if len(title_raw) > 80:
            issues.append(
                ListingValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code="EBAY_TITLE_LENGTH",
                    field="marketplace_title",
                    message="eBay titles are commonly limited to 80 characters",
                )
            )
        errors = [i for i in issues if i.severity == ValidationSeverity.ERROR]
        return ListingValidationResult(
            passed=len(errors) == 0,
            validator_name=self.name,
            issues=issues,
            summary="OK" if not errors else f"{len(errors)} eBay policy issue(s)",
        )
