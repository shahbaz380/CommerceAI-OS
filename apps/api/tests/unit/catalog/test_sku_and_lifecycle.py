"""Catalog domain unit tests."""

import pytest

from app.domain.catalog.exceptions import InvalidProductStatusTransitionError
from app.domain.catalog.lifecycle import assert_product_transition
from app.domain.catalog.sku import normalize_sku, validate_sku
from app.domain.listings.lifecycle import assert_listing_transition
from app.domain.listings.exceptions import InvalidListingStatusTransitionError
from app.shared.exceptions import ValidationAppError


def test_sku_normalize_and_validate() -> None:
    assert validate_sku(" abc-123 ") == "ABC-123"
    assert normalize_sku("a b") == "A-B"


def test_sku_invalid() -> None:
    with pytest.raises(ValidationAppError):
        validate_sku("!!")


def test_product_transition_ok() -> None:
    assert assert_product_transition("draft", "active").value == "active"


def test_product_transition_invalid() -> None:
    with pytest.raises(InvalidProductStatusTransitionError):
        assert_product_transition("archived", "active")


def test_listing_transition_ok() -> None:
    assert assert_listing_transition("draft", "ready_for_review").value == "ready_for_review"


def test_listing_transition_invalid() -> None:
    with pytest.raises(InvalidListingStatusTransitionError):
        assert_listing_transition("draft", "published")
