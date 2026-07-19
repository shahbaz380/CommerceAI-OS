"""Product catalog and listing management foundation.

Revision ID: 20260718_0005
Revises: 20260716_0004
Create Date: 2026-07-18
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.infrastructure.database.types.guid import GUID

revision: str = "20260718_0005"
down_revision: str | None = "20260716_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("internal_title", sa.String(255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("brand", sa.String(120), nullable=True),
        sa.Column("manufacturer", sa.String(120), nullable=True),
        sa.Column("model_number", sa.String(120), nullable=True),
        sa.Column("product_type", sa.String(64), nullable=True),
        sa.Column("condition", sa.String(32), server_default="new", nullable=False),
        sa.Column("status", sa.String(32), server_default="draft", nullable=False),
        sa.Column("default_sku", sa.String(64), nullable=True),
        sa.Column("country_of_origin", sa.String(2), nullable=True),
        sa.Column("weight_value", sa.Numeric(12, 4), nullable=True),
        sa.Column("weight_unit", sa.String(16), nullable=True),
        sa.Column("length_value", sa.Numeric(12, 4), nullable=True),
        sa.Column("width_value", sa.Numeric(12, 4), nullable=True),
        sa.Column("height_value", sa.Numeric(12, 4), nullable=True),
        sa.Column("dimension_unit", sa.String(16), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", GUID(), nullable=True),
        sa.Column("updated_by", GUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.UniqueConstraint("workspace_id", "default_sku", name="uq_products_workspace_default_sku"),
    )
    op.create_index("ix_products_workspace_id", "products", ["workspace_id"])
    op.create_index("ix_products_organization_id", "products", ["organization_id"])
    op.create_index("ix_products_status", "products", ["status"])
    op.create_index("ix_products_brand", "products", ["brand"])
    op.create_index("ix_products_product_type", "products", ["product_type"])
    op.create_index("ix_products_default_sku", "products", ["default_sku"])

    op.create_table(
        "product_variants",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("product_id", GUID(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sku", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("option_values", sa.JSON(), nullable=True),
        sa.Column("barcode", sa.String(64), nullable=True),
        sa.Column("mpn", sa.String(64), nullable=True),
        sa.Column("weight_value", sa.Numeric(12, 4), nullable=True),
        sa.Column("weight_unit", sa.String(16), nullable=True),
        sa.Column("length_value", sa.Numeric(12, 4), nullable=True),
        sa.Column("width_value", sa.Numeric(12, 4), nullable=True),
        sa.Column("height_value", sa.Numeric(12, 4), nullable=True),
        sa.Column("dimension_unit", sa.String(16), nullable=True),
        sa.Column("cost_amount", sa.Numeric(14, 4), nullable=True),
        sa.Column("cost_currency", sa.String(8), nullable=True),
        sa.Column("status", sa.String(32), server_default="active", nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.UniqueConstraint("workspace_id", "sku", name="uq_product_variants_workspace_sku"),
    )
    op.create_index("ix_product_variants_workspace_id", "product_variants", ["workspace_id"])
    op.create_index("ix_product_variants_product_id", "product_variants", ["product_id"])
    op.create_index("ix_product_variants_sku", "product_variants", ["sku"])

    op.create_table(
        "product_identifiers",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("product_id", GUID(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("variant_id", GUID(), sa.ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=True),
        sa.Column("identifier_type", sa.String(16), nullable=False),
        sa.Column("value", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "workspace_id", "identifier_type", "value", name="uq_product_identifiers_ws_type_value"
        ),
    )
    op.create_index("ix_product_identifiers_product_id", "product_identifiers", ["product_id"])
    op.create_index("ix_product_identifiers_value", "product_identifiers", ["value"])

    op.create_table(
        "product_attribute_definitions",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("data_type", sa.String(32), nullable=False),
        sa.Column("is_required", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_searchable", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_variant_defining", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("enum_options", sa.JSON(), nullable=True),
        sa.Column("marketplace_mapping", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("workspace_id", "code", name="uq_product_attr_def_ws_code"),
    )

    op.create_table(
        "product_attribute_values",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("product_id", GUID(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("variant_id", GUID(), sa.ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=True),
        sa.Column(
            "attribute_definition_id",
            GUID(),
            sa.ForeignKey("product_attribute_definitions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("value_text", sa.Text(), nullable=True),
        sa.Column("value_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_product_attribute_values_product_id", "product_attribute_values", ["product_id"])

    op.create_table(
        "product_categories",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("parent_id", GUID(), sa.ForeignKey("product_categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("path", sa.String(1000), server_default="", nullable=False),
        sa.Column("depth", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(32), server_default="active", nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("marketplace_mapping", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.UniqueConstraint("workspace_id", "slug", name="uq_product_categories_ws_slug"),
    )
    op.create_index("ix_product_categories_workspace_id", "product_categories", ["workspace_id"])
    op.create_index("ix_product_categories_parent_id", "product_categories", ["parent_id"])

    op.create_table(
        "product_category_assignments",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("product_id", GUID(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", GUID(), sa.ForeignKey("product_categories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.UniqueConstraint("product_id", "category_id", name="uq_product_category_assignment"),
    )
    op.create_index("ix_product_category_assignments_product_id", "product_category_assignments", ["product_id"])
    op.create_index("ix_product_category_assignments_category_id", "product_category_assignments", ["category_id"])

    op.create_table(
        "product_media",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("product_id", GUID(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("variant_id", GUID(), sa.ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=True),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column("storage_key", sa.String(500), nullable=True),
        sa.Column("file_name", sa.String(255), nullable=True),
        sa.Column("mime_type", sa.String(128), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("alt_text", sa.String(255), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("status", sa.String(32), server_default="active", nullable=False),
        sa.Column("checksum", sa.String(128), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_product_media_product_id", "product_media", ["product_id"])
    op.create_index("ix_product_media_workspace_id", "product_media", ["workspace_id"])

    op.create_table(
        "listings",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("product_id", GUID(), sa.ForeignKey("products.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("product_variant_id", GUID(), sa.ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True),
        sa.Column(
            "marketplace_connection_id",
            GUID(),
            sa.ForeignKey("marketplace_connections.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("marketplace_type", sa.String(32), nullable=True),
        sa.Column("external_listing_id", sa.String(128), nullable=True),
        sa.Column("internal_title", sa.String(255), nullable=False),
        sa.Column("marketplace_title", sa.String(255), nullable=True),
        sa.Column("subtitle", sa.String(255), nullable=True),
        sa.Column("listing_format", sa.String(32), server_default="fixed_price", nullable=False),
        sa.Column("condition", sa.String(32), nullable=True),
        sa.Column("category_id", GUID(), sa.ForeignKey("product_categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("currency", sa.String(8), server_default="USD", nullable=False),
        sa.Column("price_amount", sa.Numeric(14, 4), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(32), server_default="draft", nullable=False),
        sa.Column("publication_status", sa.String(32), nullable=True),
        sa.Column("scheduled_publish_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_state", sa.Text(), nullable=True),
        sa.Column("template_id", GUID(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("validation_passed", sa.Boolean(), nullable=True),
        sa.Column("created_by", GUID(), nullable=True),
        sa.Column("updated_by", GUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
    )
    op.create_index("ix_listings_workspace_id", "listings", ["workspace_id"])
    op.create_index("ix_listings_product_id", "listings", ["product_id"])
    op.create_index("ix_listings_status", "listings", ["status"])
    op.create_index("ix_listings_marketplace_type", "listings", ["marketplace_type"])
    op.create_index("ix_listings_external_listing_id", "listings", ["external_listing_id"])

    op.create_table(
        "listing_content",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("listing_id", GUID(), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("bullet_points", sa.JSON(), nullable=True),
        sa.Column("condition_description", sa.Text(), nullable=True),
        sa.Column("search_keywords", sa.JSON(), nullable=True),
        sa.Column("custom_fields", sa.JSON(), nullable=True),
        sa.Column("item_specifics", sa.JSON(), nullable=True),
        sa.Column("media_refs", sa.JSON(), nullable=True),
        sa.Column("marketplace_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("listing_id", name="uq_listing_content_listing"),
    )

    op.create_table(
        "listing_templates",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("marketplace_type", sa.String(32), nullable=True),
        sa.Column("listing_format", sa.String(32), server_default="fixed_price", nullable=False),
        sa.Column("title_template", sa.String(255), nullable=True),
        sa.Column("description_template", sa.Text(), nullable=True),
        sa.Column("default_condition", sa.String(32), nullable=True),
        sa.Column("default_category_id", GUID(), nullable=True),
        sa.Column("default_metadata", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_by", GUID(), nullable=True),
        sa.Column("updated_by", GUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.UniqueConstraint("workspace_id", "name", name="uq_listing_templates_ws_name"),
    )

    op.create_table(
        "listing_marketplace_mappings",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("listing_id", GUID(), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "marketplace_connection_id",
            GUID(),
            sa.ForeignKey("marketplace_connections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("marketplace_type", sa.String(32), nullable=False),
        sa.Column("external_listing_id", sa.String(128), nullable=True),
        sa.Column("external_offer_id", sa.String(128), nullable=True),
        sa.Column("external_inventory_item_id", sa.String(128), nullable=True),
        sa.Column("marketplace_status", sa.String(64), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.UniqueConstraint("listing_id", "marketplace_connection_id", name="uq_listing_marketplace_mapping"),
    )

    op.create_table(
        "listing_versions",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("listing_id", GUID(), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("changed_fields", sa.JSON(), nullable=True),
        sa.Column("change_reason", sa.String(255), nullable=True),
        sa.Column("changed_by", GUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_listing_versions_listing_id", "listing_versions", ["listing_id"])

    op.create_table(
        "listing_validation_results",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("listing_id", GUID(), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("validator_name", sa.String(64), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_listing_validation_results_listing_id", "listing_validation_results", ["listing_id"])

    op.create_table(
        "listing_validation_issues",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column(
            "validation_result_id",
            GUID(),
            sa.ForeignKey("listing_validation_results.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("field", sa.String(128), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
    )

    op.create_table(
        "listing_status_history",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("listing_id", GUID(), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_status", sa.String(32), nullable=True),
        sa.Column("to_status", sa.String(32), nullable=False),
        sa.Column("actor_user_id", GUID(), nullable=True),
        sa.Column("reason", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_listing_status_history_listing_id", "listing_status_history", ["listing_id"])


def downgrade() -> None:
    for t in (
        "listing_status_history",
        "listing_validation_issues",
        "listing_validation_results",
        "listing_versions",
        "listing_marketplace_mappings",
        "listing_templates",
        "listing_content",
        "listings",
        "product_media",
        "product_category_assignments",
        "product_categories",
        "product_attribute_values",
        "product_attribute_definitions",
        "product_identifiers",
        "product_variants",
        "products",
    ):
        op.drop_table(t)
