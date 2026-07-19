"""Inventory API schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class InventoryCreate(BaseModel):
    sku: str = Field(min_length=3, max_length=64)
    warehouse_id: UUID | None = None
    product_id: UUID | None = None
    quantity: int = Field(default=0, ge=0)


class InventoryUpdate(BaseModel):
    sku: str | None = Field(default=None, min_length=3, max_length=64)
    warehouse_id: UUID | None = None
    product_id: UUID | None = None
    status: str | None = None
    quantity: int | None = Field(default=None, ge=0)


class ReservationCreate(BaseModel):
    inventory_id: UUID
    quantity: int = Field(ge=1)


class WarehouseCreate(BaseModel):
    code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=1, max_length=255)
    warehouse_type: str = "warehouse"


class TransferRequest(BaseModel):
    inventory_id: UUID
    source_warehouse_id: UUID
    destination_warehouse_id: UUID
    quantity: int = Field(ge=1)


class AdjustmentRequest(BaseModel):
    inventory_id: UUID
    quantity: int = Field(ge=1)
    reason: str = "manual"


class InventoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    organization_id: UUID
    sku: str
    warehouse_id: UUID | None = None
    product_id: UUID | None = None
    status: str
    available_quantity: int
    reserved_quantity: int
    physical_quantity: int
    created_at: datetime
    updated_at: datetime


class WarehouseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    organization_id: UUID
    code: str
    name: str
    warehouse_type: str
    status: str
    created_at: datetime
    updated_at: datetime
