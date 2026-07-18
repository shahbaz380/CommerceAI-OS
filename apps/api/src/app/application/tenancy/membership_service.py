"""Workspace membership management."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.identity.authorization import Principal
from app.application.tenancy.tenant_access import TenantAccessService
from app.domain.tenancy.enums import MembershipStatus, WorkspaceRole, WORKSPACE_ROLE_RANK
from app.infrastructure.persistence.repositories.tenancy import (
    MembershipRepository,
    TenantAuditRepository,
)
from app.shared.exceptions import ConflictError, NotFoundError, ValidationAppError


class MembershipService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.memberships = MembershipRepository(session)
        self.audit = TenantAuditRepository(session)
        self.access = TenantAccessService(session)

    async def list_members(self, principal: Principal, workspace_id: uuid.UUID) -> list:
        await self.access.require_workspace_member(principal, workspace_id)
        return await self.memberships.list_for_workspace(workspace_id)

    async def update_role(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
        role_code: str,
    ):
        ws, _ = await self.access.require_workspace_member(
            principal, workspace_id, min_role=WorkspaceRole.MANAGER
        )
        if role_code not in WORKSPACE_ROLE_RANK:
            raise ValidationAppError("Invalid role", details=[{"field": "role_code", "issue": "unknown"}])
        m = await self.memberships.get(workspace_id, user_id)
        if m is None or m.status == MembershipStatus.REMOVED:
            raise NotFoundError("Membership not found", code="MEMBERSHIP_NOT_FOUND")
        if m.role_code == WorkspaceRole.OWNER and role_code != WorkspaceRole.OWNER:
            owners = await self.memberships.list_owners(workspace_id)
            if len(owners) <= 1:
                raise ValidationAppError(
                    "Cannot demote the only owner",
                    details=[{"field": "role", "issue": "last_owner"}],
                )
        old = m.role_code
        m.role_code = role_code
        await self.audit.add(
            event_type="membership.role_changed",
            message=f"Role changed {old} -> {role_code}",
            actor_user_id=principal.user_id,
            organization_id=ws.organization_id,
            workspace_id=workspace_id,
            metadata={"user_id": str(user_id), "old": old, "new": role_code},
        )
        await self.session.flush()
        return m

    async def suspend(self, principal: Principal, workspace_id: uuid.UUID, user_id: uuid.UUID):
        ws, _ = await self.access.require_workspace_member(
            principal, workspace_id, min_role=WorkspaceRole.MANAGER
        )
        if user_id == principal.user_id:
            raise ValidationAppError("Cannot suspend yourself", details=[{"field": "user_id", "issue": "self"}])
        m = await self.memberships.get(workspace_id, user_id)
        if m is None:
            raise NotFoundError("Membership not found", code="MEMBERSHIP_NOT_FOUND")
        m.status = MembershipStatus.SUSPENDED
        await self.audit.add(
            event_type="membership.suspended",
            message="Member suspended",
            actor_user_id=principal.user_id,
            organization_id=ws.organization_id,
            workspace_id=workspace_id,
            metadata={"user_id": str(user_id)},
        )
        await self.session.flush()
        return m

    async def remove(self, principal: Principal, workspace_id: uuid.UUID, user_id: uuid.UUID):
        ws, _ = await self.access.require_workspace_member(
            principal, workspace_id, min_role=WorkspaceRole.MANAGER
        )
        m = await self.memberships.get(workspace_id, user_id)
        if m is None:
            raise NotFoundError("Membership not found", code="MEMBERSHIP_NOT_FOUND")
        if m.role_code == WorkspaceRole.OWNER:
            owners = await self.memberships.list_owners(workspace_id)
            if len(owners) <= 1:
                raise ValidationAppError(
                    "Cannot remove the only owner",
                    details=[{"field": "user_id", "issue": "last_owner"}],
                )
        m.status = MembershipStatus.REMOVED
        await self.audit.add(
            event_type="membership.removed",
            message="Member removed",
            actor_user_id=principal.user_id,
            organization_id=ws.organization_id,
            workspace_id=workspace_id,
            metadata={"user_id": str(user_id)},
        )
        await self.session.flush()
        return m

    async def transfer_ownership(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        new_owner_user_id: uuid.UUID,
    ):
        ws, _ = await self.access.require_workspace_member(
            principal, workspace_id, min_role=WorkspaceRole.OWNER
        )
        target = await self.memberships.get(workspace_id, new_owner_user_id)
        if target is None or target.status != MembershipStatus.ACTIVE:
            raise NotFoundError("Target member not found", code="MEMBERSHIP_NOT_FOUND")
        current = await self.memberships.get(workspace_id, principal.user_id)
        if current is None:
            raise AuthorizationError_safe()
        target.role_code = WorkspaceRole.OWNER
        if current.user_id != new_owner_user_id:
            current.role_code = WorkspaceRole.MANAGER
        await self.audit.add(
            event_type="membership.ownership_transferred",
            message="Workspace ownership transferred",
            actor_user_id=principal.user_id,
            organization_id=ws.organization_id,
            workspace_id=workspace_id,
            metadata={"new_owner": str(new_owner_user_id)},
        )
        await self.session.flush()
        return target


def AuthorizationError_safe():
    from app.shared.exceptions import AuthorizationError

    raise AuthorizationError("Not a member", code="WORKSPACE_ACCESS_DENIED")
