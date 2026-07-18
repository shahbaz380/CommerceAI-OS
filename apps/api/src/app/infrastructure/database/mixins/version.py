"""Optimistic locking via version column."""

from __future__ import annotations

from typing import Any

from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column


class VersionMixin:
    """Integer version column for optimistic concurrency.

    Concrete mapped classes should include mapper args, e.g.::

        class Order(AuditedTenantModel):
            __tablename__ = "orders"
            __mapper_args__ = optimistic_lock_mapper_args()

    Or set ``__mapper_args__ = {"version_id_col": version}`` after column is defined
    on a non-abstract class. Abstract mixins cannot always bind version_id_col
    reliably across SQLAlchemy versions.
    """

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )


def optimistic_lock_mapper_args() -> dict[str, Any]:
    """Return mapper args referencing VersionMixin.version on the concrete class.

    Usage on concrete model::

        __mapper_args__ = {"version_id_col": VersionMixin.version}
    """
    return {"version_id_col": VersionMixin.version}
