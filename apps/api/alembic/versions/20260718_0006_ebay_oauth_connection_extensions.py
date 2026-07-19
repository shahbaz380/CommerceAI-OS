"""Extend marketplace connections for eBay OAuth lifecycle.

Revision ID: 20260718_0006
Revises: 20260718_0005
Create Date: 2026-07-18
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.infrastructure.database.types.guid import GUID

revision: str = "20260718_0006"
down_revision: str | None = "20260718_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "marketplace_connections",
        sa.Column("is_default", sa.Boolean(), server_default="false", nullable=False),
    )
    op.add_column("marketplace_connections", sa.Column("alias", sa.String(length=120), nullable=True))
    op.add_column("marketplace_connections", sa.Column("region", sa.String(length=32), nullable=True))
    op.add_column(
        "marketplace_connections",
        sa.Column("last_validated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "marketplace_connections",
        sa.Column("last_refreshed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "marketplace_connections",
        sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.add_column("marketplace_oauth_states", sa.Column("nonce", sa.String(length=128), nullable=True))
    op.add_column("marketplace_oauth_states", sa.Column("connection_id", GUID(), nullable=True))
    op.create_index(
        "ix_marketplace_oauth_states_connection_id",
        "marketplace_oauth_states",
        ["connection_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_marketplace_oauth_states_connection_id", table_name="marketplace_oauth_states")
    op.drop_column("marketplace_oauth_states", "connection_id")
    op.drop_column("marketplace_oauth_states", "nonce")
    op.drop_column("marketplace_connections", "suspended_at")
    op.drop_column("marketplace_connections", "last_refreshed_at")
    op.drop_column("marketplace_connections", "last_validated_at")
    op.drop_column("marketplace_connections", "region")
    op.drop_column("marketplace_connections", "alias")
    op.drop_column("marketplace_connections", "is_default")
