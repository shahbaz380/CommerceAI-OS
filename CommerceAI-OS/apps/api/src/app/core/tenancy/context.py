"""Tenant resolution from headers — foundation only.

When authentication is implemented, tenant must be derived from membership claims,
not solely from client-supplied headers.
"""

from __future__ import annotations

from uuid import UUID

from app.shared.types.context import TenantContext


def resolve_tenant_from_headers(
    workspace_header: str | None,
    *,
    enforcement: bool = True,
) -> TenantContext:
    if not workspace_header:
        return TenantContext(workspace_id=None)
    try:
        workspace_id = UUID(workspace_header)
    except ValueError:
        if enforcement:
            from app.shared.exceptions import ValidationAppError

            raise ValidationAppError(
                "Invalid workspace id header",
                details=[{"field": "workspace_id", "issue": "invalid_uuid"}],
            ) from None
        return TenantContext(workspace_id=None)
    return TenantContext(workspace_id=workspace_id)
