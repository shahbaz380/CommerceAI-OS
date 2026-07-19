"""Listing status transition rules."""

from __future__ import annotations

from app.domain.listings.enums import LISTING_TRANSITIONS, ListingStatus
from app.domain.listings.exceptions import InvalidListingStatusTransitionError


def assert_listing_transition(current: str | ListingStatus, target: str | ListingStatus) -> ListingStatus:
    cur = ListingStatus(current)
    tgt = ListingStatus(target)
    if tgt == cur:
        return cur
    allowed = LISTING_TRANSITIONS.get(cur, set())
    if tgt not in allowed:
        raise InvalidListingStatusTransitionError(cur.value, tgt.value)
    return tgt
