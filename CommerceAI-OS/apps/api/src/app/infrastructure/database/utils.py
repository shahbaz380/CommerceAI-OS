"""Database utilities — naming helpers, load strategies, index guidelines."""

from __future__ import annotations

from typing import Any

from sqlalchemy import Select
from sqlalchemy.orm import selectinload


def apply_limit_offset(stmt: Select[Any], *, offset: int = 0, limit: int = 50, max_limit: int = 500) -> Select[Any]:
    """Clamp pagination for list queries."""
    limit = max(1, min(limit, max_limit))
    offset = max(0, offset)
    return stmt.offset(offset).limit(limit)


def with_selectinloads(stmt: Select[Any], *relationships: Any) -> Select[Any]:
    """Eager-load relationships via selectinload (avoids N+1 on collections)."""
    for rel in relationships:
        stmt = stmt.options(selectinload(rel))
    return stmt


# Index strategy guidelines (for future migrations):
INDEX_GUIDELINES = """
1. Always lead multi-tenant indexes with workspace_id.
2. Partial indexes for active rows: WHERE deleted_at IS NULL.
3. Unique business keys: UNIQUE (workspace_id, external_id).
4. Time-series: (workspace_id, created_at DESC).
5. Avoid low-cardinality sole indexes (status alone).
6. Covering indexes only for proven hot paths.
"""


def tenant_unique_constraint_name(table: str, *cols: str) -> str:
    joined = "_".join(cols)
    return f"uq_{table}_workspace_{joined}"
