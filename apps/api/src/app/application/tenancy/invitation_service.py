"""Workspace invitation service."""

from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.identity.authorization import Principal
from app.application.tenancy.tenant_access import TenantAccessService
from app.domain.identity.policies import validate_email_format
from app.domain.tenancy.enums import InvitationStatus, MembershipStatus, WorkspaceRole, WORKSPACE_ROLE_RANK
from app.infrastructure.persistence.models.tenancy import (
    WorkspaceInvitationModel,
    WorkspaceMembershipModel,
)
from app.infrastructure.persistence.repositories.identity import UserRepository
from app.infrastructure.persistence.repositories.tenancy import (
    InvitationRepository,
    MembershipRepository,
    TenantAuditRepository,
)
from app.infrastructure.security.tokens import hash_token
from app.shared.exceptions import ConflictError, NotFoundError, ValidationAppError


class InvitationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.invitations = InvitationRepository(session)
        self.memberships = MembershipRepository(session)
        self.users = UserRepository(session)
        self.audit = TenantAuditRepository(session)
        self.access = TenantAccessService(session)

    async def invite(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        *,
        email: str,
        role_code: str = WorkspaceRole.STAFF,
        message: str | None = None,
        expires_days: int = 7,
    ) -> tuple[WorkspaceInvitationModel, str]:
        """Returns (invitation, raw_token) — raw token only once for delivery."""
        ws, _ = await self.access.require_workspace_member(
            principal, workspace_id, min_role=WorkspaceRole.MANAGER
        )
        email = validate_email_format(email)
        if role_code not in WORKSPACE_ROLE_RANK:
            raise ValidationAppError("Invalid role", details=[{"field": "role_code", "issue": "unknown"}])
        if role_code == WorkspaceRole.OWNER:
            raise ValidationAppError(
                "Cannot invite as owner; transfer ownership instead",
                details=[{"field": "role_code", "issue": "owner_invite"}],
            )

        existing_user = await self.users.get_by_email(email)
        if existing_user:
            m = await self.memberships.get(workspace_id, existing_user.id)
            if m and m.status == MembershipStatus.ACTIVE:
                raise ConflictError("User is already a member", code="ALREADY_MEMBER")

        raw = secrets.token_urlsafe(32)
        inv = WorkspaceInvitationModel(
            workspace_id=workspace_id,
            email=email,
            role_code=role_code,
            token_hash=hash_token(raw),
            status=InvitationStatus.PENDING,
            invited_by=principal.user_id,
            expires_at=datetime.now(UTC) + timedelta(days=expires_days),
            message=message,
        )
        await self.invitations.add(inv)
        await self.audit.add(
            event_type="invitation.sent",
            message=f"Invitation sent to {email}",
            actor_user_id=principal.user_id,
            organization_id=ws.organization_id,
            workspace_id=workspace_id,
            metadata={"email": email, "role": role_code},
        )
        await self.session.flush()
        return inv, raw

    async def list_pending(self, principal: Principal, workspace_id: uuid.UUID) -> list[WorkspaceInvitationModel]:
        await self.access.require_workspace_member(
            principal, workspace_id, min_role=WorkspaceRole.MANAGER
        )
        return await self.invitations.list_pending_for_workspace(workspace_id)

    async def accept(self, principal: Principal, *, token: str) -> WorkspaceMembershipModel:
        inv = await self.invitations.get_by_token_hash(hash_token(token))
        if inv is None:
            raise NotFoundError("Invitation not found", code="INVITATION_NOT_FOUND")
        if inv.status != InvitationStatus.PENDING:
            raise ValidationAppError("Invitation is not pending", details=[{"field": "status", "issue": inv.status}])
        exp = inv.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=UTC)
        if exp < datetime.now(UTC):
            inv.status = InvitationStatus.EXPIRED
            await self.session.flush()
            raise ValidationAppError("Invitation expired", details=[{"field": "status", "issue": "expired"}])
        if inv.email.lower() != principal.email.lower() and not principal.is_superuser:
            raise ValidationAppError(
                "Invitation email does not match authenticated user",
                details=[{"field": "email", "issue": "mismatch"}],
            )

        existing = await self.memberships.get(inv.workspace_id, principal.user_id)
        if existing and existing.status == MembershipStatus.ACTIVE:
            inv.status = InvitationStatus.ACCEPTED
            inv.accepted_at = datetime.now(UTC)
            inv.accepted_by_user_id = principal.user_id
            await self.session.flush()
            return existing

        if existing:
            existing.status = MembershipStatus.ACTIVE
            existing.role_code = inv.role_code
            existing.joined_at = datetime.now(UTC)
            membership = existing
        else:
            membership = WorkspaceMembershipModel(
                workspace_id=inv.workspace_id,
                user_id=principal.user_id,
                role_code=inv.role_code,
                status=MembershipStatus.ACTIVE,
                invited_by=inv.invited_by,
                joined_at=datetime.now(UTC),
            )
            await self.memberships.add(membership)

        inv.status = InvitationStatus.ACCEPTED
        inv.accepted_at = datetime.now(UTC)
        inv.accepted_by_user_id = principal.user_id
        await self.audit.add(
            event_type="invitation.accepted",
            message="Invitation accepted",
            actor_user_id=principal.user_id,
            workspace_id=inv.workspace_id,
            metadata={"invitation_id": str(inv.id)},
        )
        await self.session.flush()
        return membership

    async def reject(self, principal: Principal, *, token: str) -> None:
        inv = await self.invitations.get_by_token_hash(hash_token(token))
        if inv is None:
            raise NotFoundError("Invitation not found", code="INVITATION_NOT_FOUND")
        if inv.email.lower() != principal.email.lower() and not principal.is_superuser:
            raise ValidationAppError("Invitation email mismatch", details=[{"field": "email", "issue": "mismatch"}])
        inv.status = InvitationStatus.REJECTED
        await self.audit.add(
            event_type="invitation.rejected",
            message="Invitation rejected",
            actor_user_id=principal.user_id,
            workspace_id=inv.workspace_id,
        )
        await self.session.flush()

    async def revoke(self, principal: Principal, invitation_id: uuid.UUID) -> None:
        inv = await self.invitations.get_by_id(invitation_id)
        if inv is None:
            raise NotFoundError("Invitation not found", code="INVITATION_NOT_FOUND")
        ws, _ = await self.access.require_workspace_member(
            principal, inv.workspace_id, min_role=WorkspaceRole.MANAGER
        )
        inv.status = InvitationStatus.REVOKED
        await self.audit.add(
            event_type="invitation.revoked",
            message="Invitation revoked",
            actor_user_id=principal.user_id,
            organization_id=ws.organization_id,
            workspace_id=inv.workspace_id,
        )
        await self.session.flush()
