"""Product catalog ORM models — marketplace-independent source of truth."""

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


class ProductModel(SoftDeleteModel, TenantOwnedMixin, AuditUserMixin, VersionMixin):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("workspace_id", "default_sku", name="uq_products_workspace_default_sku"),
    )
    __mapper_args__ = {"version_id_col": VersionMixin.version}

    organization_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    internal_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    brand: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    manufacturer: Mapped[str | None] = mapped_column(String(120), nullable=True)
    model_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    product_type: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    condition: Mapped[str] = mapped_column(String(32), default="new", server_default="new", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="draft", server_default="draft", nullable=False, index=True)
    default_sku: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    country_of_origin: Mapped[str | None] = mapped_column(String(2), nullable=True)
    weight_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    weight_unit: Mapped[str | None] = mapped_column(String(16), nullable=True)
    length_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    width_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    height_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    dimension_unit: Mapped[str | None] = mapped_column(String(16), nullable=True)
    tags: Mapped[list[Any] | None] = mapped_column(JSONType, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONType, nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ProductVariantModel(SoftDeleteModel, TenantOwnedMixin, VersionMixin):
    __tablename__ = "product_variants"
    __table_args__ = (UniqueConstraint("workspace_id", "sku", name="uq_product_variants_workspace_sku"),)
    __mapper_args__ = {"version_id_col": VersionMixin.version}

    organization_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sku: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    option_values: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    barcode: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mpn: Mapped[str | None] = mapped_column(String(64), nullable=True)
    weight_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    weight_unit: Mapped[str | None] = mapped_column(String(16), nullable=True)
    length_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    width_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    height_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    dimension_unit: Mapped[str | None] = mapped_column(String(16), nullable=True)
    cost_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    cost_currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", server_default="active", nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONType, nullable=True)


class ProductIdentifierModel(SoftDeleteModel, TenantOwnedMixin):
    __tablename__ = "product_identifiers"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "identifier_type",
            "value",
            name="uq_product_identifiers_ws_type_value",
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    variant_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=True, index=True
    )
    identifier_type: Mapped[str] = mapped_column(String(16), nullable=False)
    value: Mapped[str] = mapped_column(String(64), nullable=False, index=True)


class ProductAttributeDefinitionModel(SoftDeleteModel, TenantOwnedMixin):
    __tablename__ = "product_attribute_definitions"
    __table_args__ = (
        UniqueConstraint("workspace_id", "code", name="uq_product_attr_def_ws_code"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    data_type: Mapped[str] = mapped_column(String(32), nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    is_searchable: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    is_variant_defining: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    enum_options: Mapped[list[Any] | None] = mapped_column(JSONType, nullable=True)
    marketplace_mapping: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONType, nullable=True)


class ProductAttributeValueModel(SoftDeleteModel, TenantOwnedMixin):
    __tablename__ = "product_attribute_values"

    organization_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    variant_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=True
    )
    attribute_definition_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("product_attribute_definitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_json: Mapped[Any | None] = mapped_column(JSONType, nullable=True)


class ProductCategoryModel(SoftDeleteModel, TenantOwnedMixin, VersionMixin):
    __tablename__ = "product_categories"
    __table_args__ = (UniqueConstraint("workspace_id", "slug", name="uq_product_categories_ws_slug"),)
    __mapper_args__ = {"version_id_col": VersionMixin.version}

    organization_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("product_categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    path: Mapped[str] = mapped_column(String(1000), nullable=False, default="/", server_default="")
    depth: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", server_default="active", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONType, nullable=True)
    marketplace_mapping: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)


class ProductCategoryAssignmentModel(Base):
    __tablename__ = "product_category_assignments"
    __table_args__ = (
        UniqueConstraint("product_id", "category_id", name="uq_product_category_assignment"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("product_categories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ProductMediaModel(SoftDeleteModel, TenantOwnedMixin):
    __tablename__ = "product_media"

    organization_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    variant_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=True, index=True
    )
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    storage_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    alt_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", server_default="active", nullable=False)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONType, nullable=True)
