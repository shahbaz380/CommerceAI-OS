"""Repository implementations (generic base)."""

from app.infrastructure.database.repositories.base import (
    GenericRepository,
    SqlAlchemyRepository,
)
from app.infrastructure.database.repositories.specification import (
    Specification,
    TenantIdSpec,
    TrueSpec,
)

__all__ = [
    "GenericRepository",
    "SqlAlchemyRepository",
    "Specification",
    "TenantIdSpec",
    "TrueSpec",
]
