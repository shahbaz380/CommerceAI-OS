"""Audit actor fields (who created/updated)."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.types.guid import GUID


class AuditUserMixin:
    """Optional actor UUIDs — set by application services when auth exists."""

    created_by: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True)
