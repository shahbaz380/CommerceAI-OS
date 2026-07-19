"""Listing API schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ListingCreate(BaseModel):
    product_id: UUID
    product_variant_id: UUID | None = None
    marketplace_connection_id: UUID | None = None
    marketplace_type: str | None = None
    internal_title: str | None = None
    marketplace_title: str | None = None
    subtitle: str | None = None
    listing_format: str = "fixed_price"
    condition: str | None = None
    category_id: UUID | None = None
    currency: str = "USD"
    price_amount: Decimal | None = None
    quantity: int | None = None
    description: str | None = None
    bullet_points: list[str] | None = None
    condition_description: str | None = None
    search_keywords: list[str] | None = None
    custom_fields: dict[str, Any] | None = None
    item_specifics: dict[str, Any] | None = None
    media_refs: list[Any] | None = None
    marketplace_metadata: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


class ListingUpdate(BaseModel):
    internal_title: str | None = None
    marketplace_title: str | None = None
    subtitle: str | None = None
    listing_format: str | None = None
    condition: str | None = None
    category_id: UUID | None = None
    currency: str | None = None
    price_amount: Decimal | None = None
    quantity: int | None = None
    marketplace_type: str | None = None
    marketplace_connection_id: UUID | None = None
    metadata: dict[str, Any] | None = None
    description: str | None = None
    bullet_points: list[str] | None = None
    condition_description: str | None = None
    search_keywords: list[str] | None = None
    custom_fields: dict[str, Any] | None = None
    item_specifics: dict[str, Any] | None = None
    media_refs: list[Any] | None = None
    marketplace_metadata: dict[str, Any] | None = None


class ListingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    workspace_id: UUID
    product_id: UUID
    product_variant_id: UUID | None = None
    marketplace_connection_id: UUID | None = None
    marketplace_type: str | None = None
    external_listing_id: str | None = None
    internal_title: str
    marketplace_title: str | None = None
    subtitle: str | None = None
    listing_format: str
    condition: str | None = None
    category_id: UUID | None = None
    currency: str
    price_amount: Decimal | None = None
    quantity: int | None = None
    status: str
    publication_status: str | None = None
    scheduled_publish_at: datetime | None = None
    validation_passed: bool | None = None
    last_validated_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    version: int


class ListingListResponse(BaseModel):
    items: list[ListingResponse]
    total: int
    offset: int
    limit: int


class ListingScheduleRequest(BaseModel):
    scheduled_publish_at: datetime


class ListingValidationIssueResponse(BaseModel):
    severity: str
    code: str
    field: str | None = None
    message: str


class ListingValidationResponse(BaseModel):
    id: UUID
    listing_id: UUID
    passed: bool
    validator_name: str
    summary: str | None = None
    issues: list[ListingValidationIssueResponse] = Field(default_factory=list)
    created_at: datetime


class ListingPreviewResponse(BaseModel):
    listing: dict[str, Any]
    content: dict[str, Any]


class ListingVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    listing_id: UUID
    version_number: int
    changed_fields: list[Any] | None = None
    change_reason: str | None = None
    changed_by: UUID | None = None
    created_at: datetime


class ListingTemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    marketplace_type: str | None = None
    listing_format: str = "fixed_price"
    title_template: str | None = None
    description_template: str | None = None
    default_condition: str | None = None
    default_category_id: UUID | None = None
    default_metadata: dict[str, Any] | None = None


class ListingTemplateUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    marketplace_type: str | None = None
    listing_format: str | None = None
    title_template: str | None = None
    description_template: str | None = None
    default_condition: str | None = None
    default_category_id: UUID | None = None
    default_metadata: dict[str, Any] | None = None
    is_active: bool | None = None


class ListingTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    name: str
    description: str | None = None
    marketplace_type: str | None = None
    listing_format: str
    title_template: str | None = None
    description_template: str | None = None
    default_condition: str | None = None
    default_category_id: UUID | None = None
    is_active: bool
    created_at: datetime
