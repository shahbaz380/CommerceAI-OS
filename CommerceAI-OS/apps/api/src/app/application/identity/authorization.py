"""RBAC permission engine."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from app.domain.identity.roles import RoleCode
from app.shared.exceptions import AuthorizationError


@dataclass(slots=True)
class Principal:
    """Authenticated security principal for the request."""

    user_id: uuid.UUID
    email: str
    roles: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    is_superuser: bool = False
    session_id: uuid.UUID | None = None
    token_jti: str | None = None

    def has_role(self, role: str | RoleCode) -> bool:
        code = role.value if isinstance(role, RoleCode) else role
        return self.is_superuser or code in self.roles

    def has_permission(self, permission: str) -> bool:
        return self.is_superuser or permission in self.permissions

    def has_all_permissions(self, *permissions: str) -> bool:
        return all(self.has_permission(p) for p in permissions)

    def has_any_permission(self, *permissions: str) -> bool:
        return any(self.has_permission(p) for p in permissions)


class AuthorizationService:
    """Evaluates RBAC decisions for a principal."""

    def require_authenticated(self, principal: Principal | None) -> Principal:
        if principal is None:
            raise AuthorizationError("Authentication required", code="AUTH_REQUIRED")
        return principal

    def require_permission(self, principal: Principal | None, permission: str) -> Principal:
        p = self.require_authenticated(principal)
        if not p.has_permission(permission):
            raise AuthorizationError(
                "Permission denied",
                code="PERMISSION_DENIED",
                details=[{"field": "permission", "issue": permission}],
            )
        return p

    def require_any_permission(self, principal: Principal | None, *permissions: str) -> Principal:
        p = self.require_authenticated(principal)
        if not p.has_any_permission(*permissions):
            raise AuthorizationError(
                "Permission denied",
                code="PERMISSION_DENIED",
                details=[{"field": "permissions", "issue": ",".join(permissions)}],
            )
        return p

    def require_role(self, principal: Principal | None, role: str) -> Principal:
        p = self.require_authenticated(principal)
        if not p.has_role(role):
            raise AuthorizationError(
                "Role required",
                code="ROLE_REQUIRED",
                details=[{"field": "role", "issue": role}],
            )
        return p

    def require_superuser(self, principal: Principal | None) -> Principal:
        p = self.require_authenticated(principal)
        if not p.is_superuser and RoleCode.SUPER_ADMIN.value not in p.roles:
            raise AuthorizationError("Super admin required", code="SUPERUSER_REQUIRED")
        return p
