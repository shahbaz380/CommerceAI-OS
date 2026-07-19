"""Listing management ORM models — internal listing drafts & marketplace refs."""

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


class ListingModel(SoftDeleteModel, TenantOwnedMixin, AuditUserMixin, VersionMixin):
    __tablename__ = "listings"
    __mapper_args__ = {"version_id_col": VersionMixin.version}

    organization_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    product_variant_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True, index=True
    )
    marketplace_connection_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("marketplace_connections.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    marketplace_type: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    external_listing_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    internal_title: Mapped[str] = mapped_column(String(255), nullable=False)
    marketplace_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subtitle: Mapped[str | None] = mapped_column(String(255), nullable=True)
    listing_format: Mapped[str] = mapped_column(
        String(32), default="fixed_price", server_default="fixed_price", nullable=False
    )
    condition: Mapped[str | None] = mapped_column(String(32), nullable=True)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("product_categories.id", ondelete="SET NULL"), nullable=True
    )
    currency: Mapped[str] = mapped_column(String(8), default="USD", server_default="USD", nullable=False)
    price_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default="draft", server_default="draft", nullable=False, index=True
    )
    publication_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    scheduled_publish_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_state: Mapped[str | None] = mapped_column(Text, nullable=True)
    template_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONType, nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    validation_passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)


class ListingContentModel(SoftDeleteModel, TenantOwnedMixin):
    __tablename__ = "listing_content"
    __table_args__ = (UniqueConstraint("listing_id", name="uq_listing_content_listing"),)

    organization_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    listing_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    bullet_points: Mapped[list[Any] | None] = mapped_column(JSONType, nullable=True)
    condition_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    search_keywords: Mapped[list[Any] | None] = mapped_column(JSONType, nullable=True)
    custom_fields: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    item_specifics: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    media_refs: Mapped[list[Any] | None] = mapped_column(JSONType, nullable=True)
    marketplace_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)


class ListingTemplateModel(SoftDeleteModel, TenantOwnedMixin, AuditUserMixin, VersionMixin):
    __tablename__ = "listing_templates"
    __table_args__ = (UniqueConstraint("workspace_id", "name", name="uq_listing_templates_ws_name"),)
    __mapper_args__ = {"version_id_col": VersionMixin.version}

    organization_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    marketplace_type: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    listing_format: Mapped[str] = mapped_column(
        String(32), default="fixed_price", server_default="fixed_price", nullable=False
    )
    title_template: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description_template: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_condition: Mapped[str | None] = mapped_column(String(32), nullable=True)
    default_category_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True)
    default_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)


class ListingMarketplaceMappingModel(SoftDeleteModel, TenantOwnedMixin, VersionMixin):
    __tablename__ = "listing_marketplace_mappings"
    __table_args__ = (
        UniqueConstraint(
            "listing_id",
            "marketplace_connection_id",
            name="uq_listing_marketplace_mapping",
        ),
    )
    __mapper_args__ = {"version_id_col": VersionMixin.version}

    organization_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    listing_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    marketplace_connection_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("marketplace_connections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    marketplace_type: Mapped[str] = mapped_column(String(32), nullable=False)
    external_listing_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    external_offer_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    external_inventory_item_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    marketplace_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONType, nullable=True)


class ListingVersionModel(Base):
    __tablename__ = "listing_versions"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    listing_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSONType, nullable=False)
    changed_fields: Mapped[list[Any] | None] = mapped_column(JSONType, nullable=True)
    change_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    changed_by: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ListingValidationResultModel(Base):
    __tablename__ = "listing_validation_results"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    listing_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    validator_name: Mapped[str] = mapped_column(String(64), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ListingValidationIssueModel(Base):
    __tablename__ = "listing_validation_issues"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    validation_result_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("listing_validation_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    field: Mapped[str | None] = mapped_column(String(128), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)


class ListingStatusHistoryModel(Base):
    __tablename__ = "listing_status_history"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    listing_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_status: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
