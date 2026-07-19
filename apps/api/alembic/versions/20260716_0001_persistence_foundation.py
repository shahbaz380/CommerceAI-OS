"""Persistence foundation baseline (no business tables).

Revision ID: 20260716_0001
Revises:
Create Date: 2026-07-16

This revision establishes the Alembic version chain for CommerceAI OS.
Business tables are added in subsequent migrations after domain modeling.
"""

from __future__ import annotations

from collections.abc import Sequence

revision: str = "20260716_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # No business tables in Prompt 13 — infrastructure only.
    # Optional: enable useful PostgreSQL extensions when running on Postgres.
    # Using raw SQL is safe no-op on SQLite tests if guarded.
    from alembic import op

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
        # gen_random_uuid() available for future server_default UUIDs


def downgrade() -> None:
    from alembic import op

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # Do not drop pgcrypto — may be used by other schemas
        pass
