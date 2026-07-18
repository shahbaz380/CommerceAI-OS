"""UUID primary key mixin."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.types.guid import GUID


class UUIDPrimaryKeyMixin:
    """Surrogate UUID primary key for all aggregate tables."""

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        # PostgreSQL can use gen_random_uuid() via server_default later
    )

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
