"""Inventory ORM models — internal inventory + eBay mapping (no offers/orders)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.infrastructure.database.base import Base, SoftDeleteModel
from app.infrastructure.database.mixins.audit import AuditUserMixin
from app.infrastructure.database.mixins.tenant import TenantOwnedMixin
from app.infrastructure.database.mixins.version import VersionMixin
from app.infrastructure.database.types.guid import GUID

JSONType = JSON().with_variant(JSONB(), "postgresql")


class InventoryItemModel(SoftDeleteModel, TenantOwnedMixin, AuditUserMixin, VersionMixin):
    __tablename__ = "inventory_items"
    __table_args__ = (UniqueConstraint("workspace_id", "sku", name="uq_inventory_items_workspace_sku"),)
    __mapper_args__ = {"version_id_col": VersionMixin.version}

    organization_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    marketplace_connection_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("marketplace_connections.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True
    )
    product_variant_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True, index=True
    )
    sku: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    condition: Mapped[str] = mapped_column(String(64), default="NEW", server_default="NEW", nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="draft", server_default="draft", nullable=False, index=True
    )
    quantity_available: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    quantity_reserved: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    location_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(120), nullable=True)
    manufacturer: Mapped[str | None] = mapped_column(String(120), nullable=True)
    mpn: Mapped[str | None] = mapped_column(String(64), nullable=True)
    upc: Mapped[str | None] = mapped_column(String(32), nullable=True)
    ean: Mapped[str | None] = mapped_column(String(32), nullable=True)
    isbn: Mapped[str | None] = mapped_column(String(32), nullable=True)
    gtin: Mapped[str | None] = mapped_column(String(32), nullable=True)
    weight_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    weight_unit: Mapped[str | None] = mapped_column(String(16), nullable=True)
    length_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    width_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    height_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    dimension_unit: Mapped[str | None] = mapped_column(String(16), nullable=True)
    image_urls: Mapped[list[Any] | None] = mapped_column(JSONType, nullable=True)
    video_refs: Mapped[list[Any] | None] = mapped_column(JSONType, nullable=True)
    aspects: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    compliance_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    marketplace_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONType, nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_sync_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_sync_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_successful_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_failed_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    validation_passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class InventoryItemMarketplaceMappingModel(SoftDeleteModel, TenantOwnedMixin, VersionMixin):
    __tablename__ = "inventory_item_marketplace_mappings"
    __table_args__ = (
        UniqueConstraint(
            "inventory_item_id",
            "marketplace_connection_id",
            name="uq_inventory_item_marketplace_mapping",
        ),
    )
    __mapper_args__ = {"version_id_col": VersionMixin.version}

    organization_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    inventory_item_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    marketplace_connection_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("marketplace_connections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    channel: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    external_sku: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    external_inventory_item_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    sync_status: Mapped[str] = mapped_column(
        String(32), default="never", server_default="never", nullable=False, index=True
    )
    last_remote_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONType, nullable=True)


class InventorySyncHistoryModel(Base):
    __tablename__ = "inventory_sync_history"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    inventory_item_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("inventory_items.id", ondelete="SET NULL"), nullable=True, index=True
    )
    marketplace_connection_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True, index=True)
    channel: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    operation: Mapped[str] = mapped_column(String(64), nullable=False)  # push|pull|delete|bulk_push
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    request_summary: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    response_summary: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class InventoryValidationResultModel(Base):
    __tablename__ = "inventory_validation_results"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    inventory_item_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    validator_name: Mapped[str] = mapped_column(String(64), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    issues: Mapped[list[Any] | None] = mapped_column(JSONType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class InventoryStatusHistoryModel(Base):
    __tablename__ = "inventory_status_history"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    inventory_item_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_status: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class InventoryMarketplaceMetadataModel(SoftDeleteModel, TenantOwnedMixin):
    """Provider-specific metadata bag per inventory item (eBay locale, package type, etc.)."""

    __tablename__ = "inventory_marketplace_metadata"
    __table_args__ = (
        UniqueConstraint(
            "inventory_item_id",
            "channel",
            name="uq_inventory_marketplace_metadata_item_channel",
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    inventory_item_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    locale: Mapped[str | None] = mapped_column(String(16), nullable=True)
    package_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload_overrides: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONType, nullable=True)
