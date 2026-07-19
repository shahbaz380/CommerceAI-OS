"""Listing domain enumerations."""

from __future__ import annotations

from enum import StrEnum


class ListingStatus(StrEnum):
    DRAFT = "draft"
    READY_FOR_REVIEW = "ready_for_review"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    PAUSED = "paused"
    ENDED = "ended"
    FAILED = "failed"
    ARCHIVED = "archived"


class ListingFormat(StrEnum):
    FIXED_PRICE = "fixed_price"
    AUCTION = "auction"
    CLASSIFIED = "classified"


class ValidationSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


LISTING_TRANSITIONS: dict[ListingStatus, set[ListingStatus]] = {
    ListingStatus.DRAFT: {ListingStatus.READY_FOR_REVIEW, ListingStatus.ARCHIVED},
    ListingStatus.READY_FOR_REVIEW: {
        ListingStatus.APPROVED,
        ListingStatus.DRAFT,
        ListingStatus.ARCHIVED,
    },
    ListingStatus.APPROVED: {
        ListingStatus.SCHEDULED,
        ListingStatus.PUBLISHING,
        ListingStatus.DRAFT,
        ListingStatus.ARCHIVED,
    },
    ListingStatus.SCHEDULED: {
        ListingStatus.PUBLISHING,
        ListingStatus.APPROVED,
        ListingStatus.ARCHIVED,
    },
    ListingStatus.PUBLISHING: {ListingStatus.PUBLISHED, ListingStatus.FAILED},
    ListingStatus.PUBLISHED: {ListingStatus.PAUSED, ListingStatus.ENDED, ListingStatus.ARCHIVED},
    ListingStatus.PAUSED: {ListingStatus.PUBLISHED, ListingStatus.ENDED, ListingStatus.ARCHIVED},
    ListingStatus.ENDED: {ListingStatus.ARCHIVED, ListingStatus.DRAFT},
    ListingStatus.FAILED: {ListingStatus.DRAFT, ListingStatus.ARCHIVED},
    ListingStatus.ARCHIVED: set(),
}
