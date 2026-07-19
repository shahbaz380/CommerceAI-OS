"""Internal inventory foundation.

Revision ID: 20260718_0007
Revises: 20260718_0006
Create Date: 2026-07-18
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.infrastructure.database.types.guid import GUID

revision: str = "20260718_0007"
down_revision: str | None = "20260718_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "warehouses",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("tenant_id", GUID(), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("warehouse_type", sa.String(32), server_default="warehouse", nullable=False),
        sa.Column("status", sa.String(32), server_default="active", nullable=False),
        sa.Column("address_line1", sa.String(255), nullable=True),
        sa.Column("city", sa.String(128), nullable=True),
        sa.Column("country", sa.String(64), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("current_utilization", sa.Integer(), nullable=True),
        sa.Column("created_by", GUID(), nullable=True),
        sa.Column("updated_by", GUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.UniqueConstraint("workspace_id", "code", name="uq_warehouse_workspace_code"),
    )
    op.create_index("ix_warehouses_tenant_id", "warehouses", ["tenant_id"])
    op.create_index("ix_warehouses_workspace_id", "warehouses", ["workspace_id"])
    op.create_index("ix_warehouses_code", "warehouses", ["code"])
    op.create_index("ix_warehouses_warehouse_type", "warehouses", ["warehouse_type"])
    op.create_index("ix_warehouses_status", "warehouses", ["status"])

    op.create_table(
        "warehouse_locations",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("tenant_id", GUID(), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("warehouse_id", GUID(), sa.ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("location_type", sa.String(32), nullable=True),
        sa.Column("aisle", sa.String(64), nullable=True),
        sa.Column("bin", sa.String(64), nullable=True),
        sa.Column("status", sa.String(32), server_default="active", nullable=False),
        sa.Column("created_by", GUID(), nullable=True),
        sa.Column("updated_by", GUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.UniqueConstraint("workspace_id", "warehouse_id", "code", name="uq_wc_workspace_warehouse_code"),
    )
    op.create_index("ix_warehouse_locations_tenant_id", "warehouse_locations", ["tenant_id"])
    op.create_index("ix_warehouse_locations_workspace_id", "warehouse_locations", ["workspace_id"])
    op.create_index("ix_warehouse_locations_warehouse_id", "warehouse_locations", ["warehouse_id"])
    op.create_index("ix_warehouse_locations_status", "warehouse_locations", ["status"])

    op.create_table(
        "inventory",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("tenant_id", GUID(), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("product_id", GUID(), sa.ForeignKey("products.id", ondelete="SET NULL"), nullable=True),
        sa.Column("warehouse_id", GUID(), sa.ForeignKey("warehouses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("sku", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), server_default="active", nullable=False),
        sa.Column("available_quantity", sa.Integer(), server_default="0", nullable=False),
        sa.Column("reserved_quantity", sa.Integer(), server_default="0", nullable=False),
        sa.Column("physical_quantity", sa.Integer(), server_default="0", nullable=False),
        sa.Column("low_stock_threshold", sa.Integer(), nullable=True),
        sa.Column("out_of_stock_threshold", sa.Integer(), nullable=True),
        sa.Column("reorder_point", sa.Integer(), nullable=True),
        sa.Column("reorder_quantity", sa.Integer(), nullable=True),
        sa.Column("last_known_cost", sa.Numeric(12, 4), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_by", GUID(), nullable=True),
        sa.Column("updated_by", GUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.UniqueConstraint("workspace_id", "sku", name="uq_inventory_workspace_sku"),
    )
    op.create_index("ix_inventory_tenant_id", "inventory", ["tenant_id"])
    op.create_index("ix_inventory_workspace_id", "inventory", ["workspace_id"])
    op.create_index("ix_inventory_product_id", "inventory", ["product_id"])
    op.create_index("ix_inventory_warehouse_id", "inventory", ["warehouse_id"])
    op.create_index("ix_inventory_sku", "inventory", ["sku"])
    op.create_index("ix_inventory_status", "inventory", ["status"])

    op.create_table(
        "inventory_level",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("tenant_id", GUID(), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("inventory_id", GUID(), sa.ForeignKey("inventory.id", ondelete="CASCADE"), nullable=False),
        sa.Column("warehouse_id", GUID(), sa.ForeignKey("warehouses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("sku", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), server_default="active", nullable=False),
        sa.Column("available_quantity", sa.Integer(), server_default="0", nullable=False),
        sa.Column("reserved_quantity", sa.Integer(), server_default="0", nullable=False),
        sa.Column("physical_quantity", sa.Integer(), server_default="0", nullable=False),
        sa.Column("low_stock_threshold", sa.Integer(), nullable=True),
        sa.Column("out_of_stock_threshold", sa.Integer(), nullable=True),
        sa.Column("created_by", GUID(), nullable=True),
        sa.Column("updated_by", GUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.UniqueConstraint("workspace_id", "inventory_id", "warehouse_id", name="uq_inventory_level_workspace_inventory_warehouse"),
    )
    op.create_index("ix_inventory_level_inventory_id", "inventory_level", ["inventory_id"])
    op.create_index("ix_inventory_level_warehouse_id", "inventory_level", ["warehouse_id"])
    op.create_index("ix_inventory_level_sku_lookup", "inventory_level", ["sku"])

    op.create_table(
        "inventory_reservation",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("tenant_id", GUID(), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("inventory_id", GUID(), sa.ForeignKey("inventory.id", ondelete="CASCADE"), nullable=False),
        sa.Column("warehouse_id", GUID(), sa.ForeignKey("warehouses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reservation_id", GUID(), nullable=False, unique=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), server_default="active", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_by", GUID(), nullable=True),
        sa.Column("updated_by", GUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
    )
    op.create_index("ix_inventory_reservation_tenant_id", "inventory_reservation", ["tenant_id"])
    op.create_index("ix_inventory_reservation_workspace_id", "inventory_reservation", ["workspace_id"])
    op.create_index("ix_inventory_reservation_inventory_id", "inventory_reservation", ["inventory_id"])
    op.create_index("ix_inventory_reservation_status_updated", "inventory_reservation", ["status", "updated_at"])
    op.create_index("ix_inventory_reservation_reservation_id", "inventory_reservation", ["reservation_id"])

    op.create_table(
        "inventory_movement",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("tenant_id", GUID(), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("inventory_id", GUID(), sa.ForeignKey("inventory.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_warehouse_id", GUID(), sa.ForeignKey("warehouses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("destination_warehouse_id", GUID(), sa.ForeignKey("warehouses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("movement_type", sa.String(32), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(128), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_by", GUID(), nullable=True),
        sa.Column("updated_by", GUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
    )
    op.create_index("ix_inventory_movement_tenant_id", "inventory_movement", ["tenant_id"])
    op.create_index("ix_inventory_movement_workspace_id", "inventory_movement", ["workspace_id"])
    op.create_index("ix_inventory_movement_inventory_id", "inventory_movement", ["inventory_id"])
    op.create_index("ix_inventory_movement_movement_type", "inventory_movement", ["movement_type"])

    op.create_table(
        "inventory_adjustment",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("tenant_id", GUID(), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("inventory_id", GUID(), sa.ForeignKey("inventory.id", ondelete="CASCADE"), nullable=False),
        sa.Column("warehouse_id", GUID(), sa.ForeignKey("warehouses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("adjustment_type", sa.String(32), nullable=False),
        sa.Column("reason", sa.String(64), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", GUID(), nullable=True),
        sa.Column("updated_by", GUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
    )
    op.create_index("ix_inventory_adjustment_tenant_id", "inventory_adjustment", ["tenant_id"])
    op.create_index("ix_inventory_adjustment_workspace_id", "inventory_adjustment", ["workspace_id"])
    op.create_index("ix_inventory_adjustment_inventory_id", "inventory_adjustment", ["inventory_id"])
    op.create_index("ix_inventory_adjustment_reason", "inventory_adjustment", ["reason"])

    op.create_table(
        "inventory_snapshot",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("tenant_id", GUID(), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("inventory_id", GUID(), sa.ForeignKey("inventory.id", ondelete="CASCADE"), nullable=False),
        sa.Column("warehouse_id", GUID(), sa.ForeignKey("warehouses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("available_quantity", sa.Integer(), nullable=False),
        sa.Column("reserved_quantity", sa.Integer(), nullable=False),
        sa.Column("physical_quantity", sa.Integer(), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_by", GUID(), nullable=True),
        sa.Column("updated_by", GUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
    )
    op.create_index("ix_inventory_snapshot_inventory_id", "inventory_snapshot", ["inventory_id"])
    op.create_index("ix_inventory_snapshot_captured_at", "inventory_snapshot", ["captured_at"])


def downgrade() -> None:
    op.drop_index("ix_inventory_snapshot_captured_at", table_name="inventory_snapshot")
    op.drop_index("ix_inventory_snapshot_inventory_id", table_name="inventory_snapshot")
    op.drop_table("inventory_snapshot")

    op.drop_index("ix_inventory_adjustment_reason", table_name="inventory_adjustment")
    op.drop_index("ix_inventory_adjustment_inventory_id", table_name="inventory_adjustment")
    op.drop_index("ix_inventory_adjustment_workspace_id", table_name="inventory_adjustment")
    op.drop_index("ix_inventory_adjustment_tenant_id", table_name="inventory_adjustment")
    op.drop_table("inventory_adjustment")

    op.drop_index("ix_inventory_movement_movement_type", table_name="inventory_movement")
    op.drop_index("ix_inventory_movement_inventory_id", table_name="inventory_movement")
    op.drop_index("ix_inventory_movement_workspace_id", table_name="inventory_movement")
    op.drop_index("ix_inventory_movement_tenant_id", table_name="inventory_movement")
    op.drop_table("inventory_movement")

    op.drop_index("ix_inventory_reservation_reservation_id", table_name="inventory_reservation")
    op.drop_index("ix_inventory_reservation_status_updated", table_name="inventory_reservation")
    op.drop_index("ix_inventory_reservation_inventory_id", table_name="inventory_reservation")
    op.drop_index("ix_inventory_reservation_workspace_id", table_name="inventory_reservation")
    op.drop_index("ix_inventory_reservation_tenant_id", table_name="inventory_reservation")
    op.drop_table("inventory_reservation")

    op.drop_index("ix_inventory_level_sku_lookup", table_name="inventory_level")
    op.drop_index("ix_inventory_level_warehouse_id", table_name="inventory_level")
    op.drop_index("ix_inventory_level_inventory_id", table_name="inventory_level")
    op.drop_table("inventory_level")

    op.drop_index("ix_inventory_status", table_name="inventory")
    op.drop_index("ix_inventory_sku", table_name="inventory")
    op.drop_index("ix_inventory_warehouse_id", table_name="inventory")
    op.drop_index("ix_inventory_product_id", table_name="inventory")
    op.drop_index("ix_inventory_workspace_id", table_name="inventory")
    op.drop_index("ix_inventory_tenant_id", table_name="inventory")
    op.drop_table("inventory")

    op.drop_index("ix_warehouse_locations_status", table_name="warehouse_locations")
    op.drop_index("ix_warehouse_locations_warehouse_id", table_name="warehouse_locations")
    op.drop_index("ix_warehouse_locations_workspace_id", table_name="warehouse_locations")
    op.drop_index("ix_warehouse_locations_tenant_id", table_name="warehouse_locations")
    op.drop_table("warehouse_locations")

    op.drop_index("ix_warehouses_status", table_name="warehouses")
    op.drop_index("ix_warehouses_warehouse_type", table_name="warehouses")
    op.drop_index("ix_warehouses_code", table_name="warehouses")
    op.drop_index("ix_warehouses_workspace_id", table_name="warehouses")
    op.drop_index("ix_warehouses_tenant_id", table_name="warehouses")
    op.drop_table("warehouses")
