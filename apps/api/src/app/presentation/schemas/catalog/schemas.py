"""Catalog API schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    internal_title: str | None = None
    description: str | None = None
    brand: str | None = None
    manufacturer: str | None = None
    model_number: str | None = None
    product_type: str | None = None
    condition: str = "new"
    default_sku: str | None = None
    auto_sku: bool = False
    country_of_origin: str | None = Field(default=None, max_length=2)
    weight_value: Decimal | None = None
    weight_unit: str | None = None
    length_value: Decimal | None = None
    width_value: Decimal | None = None
    height_value: Decimal | None = None
    dimension_unit: str | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    internal_title: str | None = None
    description: str | None = None
    brand: str | None = None
    manufacturer: str | None = None
    model_number: str | None = None
    product_type: str | None = None
    condition: str | None = None
    default_sku: str | None = None
    country_of_origin: str | None = None
    weight_value: Decimal | None = None
    weight_unit: str | None = None
    length_value: Decimal | None = None
    width_value: Decimal | None = None
    height_value: Decimal | None = None
    dimension_unit: str | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    workspace_id: UUID
    name: str
    internal_title: str | None = None
    description: str | None = None
    brand: str | None = None
    manufacturer: str | None = None
    model_number: str | None = None
    product_type: str | None = None
    condition: str
    status: str
    default_sku: str | None = None
    country_of_origin: str | None = None
    weight_value: Decimal | None = None
    weight_unit: str | None = None
    length_value: Decimal | None = None
    width_value: Decimal | None = None
    height_value: Decimal | None = None
    dimension_unit: str | None = None
    tags: list[Any] | None = None
    metadata_json: dict[str, Any] | None = Field(default=None, validation_alias="metadata_json")
    created_at: datetime
    updated_at: datetime
    version: int


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    offset: int
    limit: int


class VariantCreate(BaseModel):
    sku: str | None = None
    title: str | None = None
    option_values: dict[str, Any] | None = None
    barcode: str | None = None
    mpn: str | None = None
    weight_value: Decimal | None = None
    weight_unit: str | None = None
    length_value: Decimal | None = None
    width_value: Decimal | None = None
    height_value: Decimal | None = None
    dimension_unit: str | None = None
    cost_amount: Decimal | None = None
    cost_currency: str | None = None
    status: str = "active"
    metadata: dict[str, Any] | None = None


class VariantUpdate(BaseModel):
    sku: str | None = None
    title: str | None = None
    option_values: dict[str, Any] | None = None
    barcode: str | None = None
    mpn: str | None = None
    weight_value: Decimal | None = None
    weight_unit: str | None = None
    length_value: Decimal | None = None
    width_value: Decimal | None = None
    height_value: Decimal | None = None
    dimension_unit: str | None = None
    cost_amount: Decimal | None = None
    cost_currency: str | None = None
    status: str | None = None
    metadata: dict[str, Any] | None = None


class VariantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    workspace_id: UUID
    sku: str
    title: str | None = None
    option_values: dict[str, Any] | None = None
    barcode: str | None = None
    mpn: str | None = None
    status: str
    cost_amount: Decimal | None = None
    cost_currency: str | None = None
    created_at: datetime


class IdentifierCreate(BaseModel):
    identifier_type: str
    value: str
    variant_id: UUID | None = None


class IdentifierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    variant_id: UUID | None = None
    identifier_type: str
    value: str


class AttributeValueCreate(BaseModel):
    attribute_definition_id: UUID
    value_text: str | None = None
    value_json: Any = None
    variant_id: UUID | None = None


class MediaCreate(BaseModel):
    url: str
    is_primary: bool = False
    mime_type: str | None = None
    storage_key: str | None = None
    file_name: str | None = None
    file_size: int | None = None
    width: int | None = None
    height: int | None = None
    alt_text: str | None = None
    sort_order: int = 0
    variant_id: UUID | None = None
    checksum: str | None = None
    metadata: dict[str, Any] | None = None


class MediaReorderRequest(BaseModel):
    ordered_ids: list[UUID]


class MediaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    variant_id: UUID | None = None
    url: str
    mime_type: str | None = None
    sort_order: int
    is_primary: bool
    status: str
    alt_text: str | None = None


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str | None = None
    parent_id: UUID | None = None
    description: str | None = None
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    parent_id: UUID | None = None
    sort_order: int | None = None
    status: str | None = None
    metadata_json: dict[str, Any] | None = None
    marketplace_mapping: dict[str, Any] | None = None


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    parent_id: UUID | None = None
    name: str
    slug: str
    path: str
    depth: int
    status: str
    sort_order: int
    description: str | None = None
