"""UUID/GUID type portable across PostgreSQL and SQLite (tests)."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import CHAR, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.engine.interfaces import Dialect


class GUID(TypeDecorator[uuid.UUID]):
    """Platform-independent UUID stored as native UUID on PostgreSQL, CHAR(36) elsewhere.

    Always bind/result as ``uuid.UUID`` in Python.
    """

    impl = CHAR(36)
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect) -> Any:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value: Any, dialect: Dialect) -> Any:
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(str(value))
        if dialect.name == "postgresql":
            return value
        return str(value)

    def process_result_value(self, value: Any, dialect: Dialect) -> uuid.UUID | None:
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))
