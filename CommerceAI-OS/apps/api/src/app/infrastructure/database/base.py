"""SQLAlchemy Declarative base and enterprise base model mixins composition.

No business tables are defined here. Feature models inherit from these bases.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass

from app.infrastructure.database.mixins.audit import AuditUserMixin
from app.infrastructure.database.mixins.primary_key import UUIDPrimaryKeyMixin
from app.infrastructure.database.mixins.soft_delete import SoftDeleteMixin
from app.infrastructure.database.mixins.tenant import TenantOwnedMixin
from app.infrastructure.database.mixins.timestamp import TimestampMixin
from app.infrastructure.database.mixins.version import VersionMixin


class Base(DeclarativeBase):
    """ORM registry root — Alembic `target_metadata = Base.metadata`."""

    pass


class MappedBase(Base):
    """Abstract non-mapped base for mixins composition without table."""

    __abstract__ = True


class TimestampedModel(UUIDPrimaryKeyMixin, TimestampMixin, MappedBase):
    """UUID PK + timestamps."""

    __abstract__ = True


class SoftDeleteModel(TimestampedModel, SoftDeleteMixin):
    """Timestamped + soft delete."""

    __abstract__ = True


class TenantModel(SoftDeleteModel, TenantOwnedMixin):
    """Tenant-owned soft-deletable aggregate root base."""

    __abstract__ = True


class AuditedTenantModel(TenantModel, AuditUserMixin, VersionMixin):
    """Full enterprise row: tenant, audit users, optimistic lock, soft delete."""

    __abstract__ = True


class SystemModel(TimestampedModel, SoftDeleteMixin, VersionMixin):
    """Non-tenant system tables (plans, global catalogs) — still soft-deletable."""

    __abstract__ = True
