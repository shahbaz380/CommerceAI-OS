"""Persistence façade — re-exports for application/infrastructure consumers."""

from app.infrastructure.database import (
    AuditedTenantModel,
    Base,
    GenericRepository,
    SoftDeleteModel,
    SqlAlchemyRepository,
    SqlAlchemyUnitOfWork,
    SystemModel,
    TenantModel,
    TimestampedModel,
    get_database,
    get_session_factory,
    init_database,
    shutdown_database,
)

__all__ = [
    "AuditedTenantModel",
    "Base",
    "GenericRepository",
    "SoftDeleteModel",
    "SqlAlchemyRepository",
    "SqlAlchemyUnitOfWork",
    "SystemModel",
    "TenantModel",
    "TimestampedModel",
    "get_database",
    "get_session_factory",
    "init_database",
    "shutdown_database",
]
