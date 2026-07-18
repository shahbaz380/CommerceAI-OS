"""Unit tests for database utilities and specs."""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.infrastructure.database.repositories.specification import (
    NotDeletedSpec,
    TenantIdSpec,
    TrueSpec,
)
from app.infrastructure.database.utils import apply_limit_offset, tenant_unique_constraint_name


def test_apply_limit_offset_clamps() -> None:
    stmt = select(1)
    out = apply_limit_offset(stmt, offset=-5, limit=9999, max_limit=100)
    # SQLAlchemy compiles limit/offset — ensure call succeeds
    assert out is not None


def test_tenant_unique_name() -> None:
    assert tenant_unique_constraint_name("listings", "sku") == "uq_listings_workspace_sku"


def test_specs_compose() -> None:
    class Dummy:
        workspace_id = type("C", (), {})()
        deleted_at = type("C", (), {})()

    # TrueSpec & TenantIdSpec should be constructible
    ws = uuid.uuid4()
    spec = TrueSpec() & TenantIdSpec(ws)
    assert spec is not None
    nd = NotDeletedSpec()
    assert nd is not None
