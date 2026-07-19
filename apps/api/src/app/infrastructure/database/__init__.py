"""Database infrastructure public API."""

from app.infrastructure.database.base import (
    AuditedTenantModel,
    Base,
    SoftDeleteModel,
    SystemModel,
    TenantModel,
    TimestampedModel,
)
from app.infrastructure.database.repositories.base import GenericRepository, SqlAlchemyRepository
from app.infrastructure.database.session import (
    Database,
    PoolStats,
    get_database,
    get_session_factory,
    init_database,
    session_scope,
    shutdown_database,
    validate_database_on_startup,
)
from app.infrastructure.database.uow.sqlalchemy_uow import SqlAlchemyUnitOfWork

__all__ = [
    "AuditedTenantModel",
    "Base",
    "Database",
    "GenericRepository",
    "PoolStats",
    "SoftDeleteModel",
    "SqlAlchemyRepository",
    "SqlAlchemyUnitOfWork",
    "SystemModel",
    "TenantModel",
    "TimestampedModel",
    "get_database",
    "get_session_factory",
    "init_database",
    "session_scope",
    "shutdown_database",
    "validate_database_on_startup",
]
