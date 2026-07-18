"""Tenant boundary enforcement helpers."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.identity.authorization import Principal
from app.domain.tenancy.enums import MembershipStatus, WorkspaceRole, role_at_least
from app.infrastructure.persistence.repositories.tenancy import (
    MembershipRepository,
    OrganizationRepository,
    WorkspaceRepository,
)
from app.shared.exceptions import AuthorizationError, NotFoundError


class TenantAccessService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.orgs = OrganizationRepository(session)
        self.workspaces = WorkspaceRepository(session)
        self.memberships = MembershipRepository(session)

    async def require_org_access(
        self,
        principal: Principal,
        organization_id: uuid.UUID,
        *,
        min_role: str | None = None,
    ) -> None:
        if principal.is_superuser:
            return
        org = await self.orgs.get_by_id(organization_id)
        if org is None:
            raise NotFoundError("Organization not found", code="ORG_NOT_FOUND")
        if org.owner_user_id == principal.user_id:
            return
        # member of any workspace in org
        workspaces = await self.workspaces.list_for_org(organization_id)
        for ws in workspaces:
            m = await self.memberships.get(ws.id, principal.user_id)
            if m and m.status == MembershipStatus.ACTIVE:
                if min_role is None or role_at_least(m.role_code, min_role):
                    return
        raise AuthorizationError("No access to organization", code="ORG_ACCESS_DENIED")

    async def require_workspace_member(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        *,
        min_role: str = WorkspaceRole.READ_ONLY,
    ) -> tuple:
        ws = await self.workspaces.get_by_id(workspace_id)
        if ws is None:
            raise NotFoundError("Workspace not found", code="WORKSPACE_NOT_FOUND")
        if principal.is_superuser:
            return ws, None
        # org owner always allowed
        org = await self.orgs.get_by_id(ws.organization_id)
        if org and org.owner_user_id == principal.user_id:
            return ws, None
        m = await self.memberships.get(workspace_id, principal.user_id)
        if m is None or m.status != MembershipStatus.ACTIVE:
            raise AuthorizationError("Not a workspace member", code="WORKSPACE_ACCESS_DENIED")
        if not role_at_least(m.role_code, min_role):
            raise AuthorizationError(
                "Insufficient workspace role",
                code="WORKSPACE_ROLE_DENIED",
                details=[{"field": "role", "issue": min_role}],
            )
        return ws, m

    async def require_org_owner(self, principal: Principal, organization_id: uuid.UUID) -> None:
        if principal.is_superuser:
            return
        org = await self.orgs.get_by_id(organization_id)
        if org is None:
            raise NotFoundError("Organization not found", code="ORG_NOT_FOUND")
        if org.owner_user_id != principal.user_id:
            raise AuthorizationError("Organization owner required", code="ORG_OWNER_REQUIRED")
