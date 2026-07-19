"""Multi-tenant ownership mixin (workspace isolation foundation)."""

from __future__ import annotations

import uuid

from sqlalchemy import Index
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.types.guid import GUID


class TenantOwnedMixin:
    """Every tenant-scoped row carries workspace_id for isolation filters.

    Enforcement of tenancy is the responsibility of repositories / UoW
    when application services pass TenantContext.
    """

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        nullable=False,
        index=True,
    )


def tenant_index(*columns: str, name: str) -> Index:
    """Build a composite index starting with workspace_id (guideline helper)."""
    cols = ("workspace_id", *columns)
    return Index(name, *cols)
