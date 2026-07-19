"""Listing validator unit tests."""

from app.infrastructure.marketplace.listing_validation.base import DefaultListingValidator
from app.infrastructure.marketplace.listing_validation.ebay import EbayListingPolicyValidator


def test_default_validator_requires_title() -> None:
    result = DefaultListingValidator().validate({"internal_title": ""}, {"description": "hello"})
    assert result.passed is False
    assert any(i.code == "TITLE_REQUIRED" for i in result.errors)


def test_default_validator_ok() -> None:
    result = DefaultListingValidator().validate(
        {
            "internal_title": "Nice Product",
            "listing_format": "fixed_price",
            "currency": "USD",
            "price_amount": "10.00",
            "quantity": 1,
            "category_id": "x",
        },
        {"description": "A solid description"},
    )
    assert result.passed is True


def test_ebay_policy_blocks_term() -> None:
    result = EbayListingPolicyValidator().validate(
        {"internal_title": "Guaranteed ranking shoes"},
        {"description": "great"},
    )
    assert result.passed is False
