"""Tenant-aware FastAPI dependencies."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.identity.authorization import Principal
from app.application.tenancy.invitation_service import InvitationService
from app.application.tenancy.membership_service import MembershipService
from app.application.tenancy.organization_service import OrganizationService
from app.application.tenancy.profile_service import ProfileService
from app.application.tenancy.tenant_access import TenantAccessService
from app.application.tenancy.workspace_service import WorkspaceService
from app.config.settings import get_settings
from app.core.tenancy.context import resolve_tenant_from_headers
from app.presentation.api.deps.auth import get_current_principal
from app.presentation.api.deps.common import get_db_session
from app.shared.types.context import TenantContext


async def get_organization_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> OrganizationService:
    return OrganizationService(session)


async def get_workspace_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> WorkspaceService:
    return WorkspaceService(session)


async def get_membership_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MembershipService:
    return MembershipService(session)


async def get_invitation_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> InvitationService:
    return InvitationService(session)


async def get_profile_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ProfileService:
    return ProfileService(session)


async def get_tenant_access(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> TenantAccessService:
    return TenantAccessService(session)


async def resolve_active_tenant(
    request: Request,
    principal: Annotated[Principal, Depends(get_current_principal)],
    access: Annotated[TenantAccessService, Depends(get_tenant_access)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> TenantContext:
    """Validate membership when workspace header present; bind to request context."""
    settings = get_settings()
    tenant = resolve_tenant_from_headers(x_workspace_id, enforcement=settings.tenancy_enforcement)
    if tenant.workspace_id is not None:
        ws, membership = await access.require_workspace_member(principal, tenant.workspace_id)
        tenant = TenantContext(
            workspace_id=ws.id,
            company_id=ws.organization_id,
            is_platform_admin=principal.is_superuser,
        )
        if hasattr(request.state, "request_context") and request.state.request_context:
            request.state.request_context.tenant = tenant
        request.state.workspace_membership = membership
        request.state.workspace = ws
    return tenant
