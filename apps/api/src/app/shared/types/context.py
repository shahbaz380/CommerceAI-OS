"""Request / tenant context value objects (no persistence)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass(slots=True, frozen=True)
class TenantContext:
    """Multi-tenant scope for the current request/job.

    Prefer resolving via authenticated membership + X-Workspace-Id header.
    """

    workspace_id: UUID | None = None
    company_id: UUID | None = None  # organization_id
    is_platform_admin: bool = False

    def require_workspace(self) -> UUID:
        if self.workspace_id is None:
            from app.shared.exceptions import AuthorizationError

            raise AuthorizationError(
                "Workspace context is required",
                code="WORKSPACE_REQUIRED",
            )
        return self.workspace_id


@dataclass(slots=True)
class RequestContext:
    """Per-request correlation metadata attached by middleware."""

    request_id: str
    correlation_id: str
    tenant: TenantContext = field(default_factory=TenantContext)
    path: str = ""
    method: str = ""
    client_ip: str | None = None
    user_agent: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)
