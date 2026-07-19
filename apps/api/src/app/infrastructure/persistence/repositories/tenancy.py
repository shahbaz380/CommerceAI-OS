"""Tenancy repositories."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.persistence.models.tenancy import (
    OrganizationModel,
    OrganizationSettingsModel,
    TenantAuditModel,
    UserProfileModel,
    WorkspaceInvitationModel,
    WorkspaceMembershipModel,
    WorkspaceModel,
    WorkspaceSettingsModel,
)


class OrganizationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, org: OrganizationModel) -> OrganizationModel:
        self.session.add(org)
        await self.session.flush()
        return org

    async def get_by_id(self, org_id: uuid.UUID) -> OrganizationModel | None:
        stmt = select(OrganizationModel).where(
            OrganizationModel.id == org_id,
            OrganizationModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> OrganizationModel | None:
        stmt = select(OrganizationModel).where(
            OrganizationModel.slug == slug,
            OrganizationModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_owner(self, owner_user_id: uuid.UUID) -> list[OrganizationModel]:
        stmt = select(OrganizationModel).where(
            OrganizationModel.owner_user_id == owner_user_id,
            OrganizationModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_for_user(self, user_id: uuid.UUID) -> list[OrganizationModel]:
        """Orgs where user is owner or member of any workspace."""
        stmt = (
            select(OrganizationModel)
            .join(WorkspaceModel, WorkspaceModel.organization_id == OrganizationModel.id)
            .join(WorkspaceMembershipModel, WorkspaceMembershipModel.workspace_id == WorkspaceModel.id)
            .where(
                WorkspaceMembershipModel.user_id == user_id,
                WorkspaceMembershipModel.status == "active",
                OrganizationModel.deleted_at.is_(None),
                WorkspaceModel.deleted_at.is_(None),
            )
            .distinct()
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class WorkspaceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, ws: WorkspaceModel) -> WorkspaceModel:
        self.session.add(ws)
        await self.session.flush()
        return ws

    async def get_by_id(self, workspace_id: uuid.UUID) -> WorkspaceModel | None:
        stmt = (
            select(WorkspaceModel)
            .where(WorkspaceModel.id == workspace_id, WorkspaceModel.deleted_at.is_(None))
            .options(selectinload(WorkspaceModel.organization))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_org_slug(self, organization_id: uuid.UUID, slug: str) -> WorkspaceModel | None:
        stmt = select(WorkspaceModel).where(
            WorkspaceModel.organization_id == organization_id,
            WorkspaceModel.slug == slug,
            WorkspaceModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_org(self, organization_id: uuid.UUID) -> list[WorkspaceModel]:
        stmt = select(WorkspaceModel).where(
            WorkspaceModel.organization_id == organization_id,
            WorkspaceModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_for_user(self, user_id: uuid.UUID) -> list[WorkspaceModel]:
        stmt = (
            select(WorkspaceModel)
            .join(WorkspaceMembershipModel)
            .where(
                WorkspaceMembershipModel.user_id == user_id,
                WorkspaceMembershipModel.status == "active",
                WorkspaceModel.deleted_at.is_(None),
            )
            .options(selectinload(WorkspaceModel.organization))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class MembershipRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, m: WorkspaceMembershipModel) -> WorkspaceMembershipModel:
        self.session.add(m)
        await self.session.flush()
        return m

    async def get(self, workspace_id: uuid.UUID, user_id: uuid.UUID) -> WorkspaceMembershipModel | None:
        stmt = select(WorkspaceMembershipModel).where(
            WorkspaceMembershipModel.workspace_id == workspace_id,
            WorkspaceMembershipModel.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_workspace(self, workspace_id: uuid.UUID) -> list[WorkspaceMembershipModel]:
        stmt = select(WorkspaceMembershipModel).where(
            WorkspaceMembershipModel.workspace_id == workspace_id,
            WorkspaceMembershipModel.status != "removed",
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_owners(self, workspace_id: uuid.UUID) -> list[WorkspaceMembershipModel]:
        stmt = select(WorkspaceMembershipModel).where(
            WorkspaceMembershipModel.workspace_id == workspace_id,
            WorkspaceMembershipModel.role_code == "organization_owner",
            WorkspaceMembershipModel.status == "active",
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class InvitationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, inv: WorkspaceInvitationModel) -> WorkspaceInvitationModel:
        self.session.add(inv)
        await self.session.flush()
        return inv

    async def get_by_token_hash(self, token_hash: str) -> WorkspaceInvitationModel | None:
        stmt = select(WorkspaceInvitationModel).where(WorkspaceInvitationModel.token_hash == token_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, invitation_id: uuid.UUID) -> WorkspaceInvitationModel | None:
        stmt = select(WorkspaceInvitationModel).where(WorkspaceInvitationModel.id == invitation_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_pending_for_workspace(self, workspace_id: uuid.UUID) -> list[WorkspaceInvitationModel]:
        stmt = select(WorkspaceInvitationModel).where(
            WorkspaceInvitationModel.workspace_id == workspace_id,
            WorkspaceInvitationModel.status == "pending",
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_pending_for_email(self, email: str) -> list[WorkspaceInvitationModel]:
        stmt = select(WorkspaceInvitationModel).where(
            WorkspaceInvitationModel.email == email.lower(),
            WorkspaceInvitationModel.status == "pending",
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class ProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_user_id(self, user_id: uuid.UUID) -> UserProfileModel | None:
        stmt = select(UserProfileModel).where(UserProfileModel.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add(self, profile: UserProfileModel) -> UserProfileModel:
        self.session.add(profile)
        await self.session.flush()
        return profile


class OrgSettingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, organization_id: uuid.UUID) -> OrganizationSettingsModel | None:
        stmt = select(OrganizationSettingsModel).where(
            OrganizationSettingsModel.organization_id == organization_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add(self, row: OrganizationSettingsModel) -> OrganizationSettingsModel:
        self.session.add(row)
        await self.session.flush()
        return row


class WorkspaceSettingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, workspace_id: uuid.UUID) -> WorkspaceSettingsModel | None:
        stmt = select(WorkspaceSettingsModel).where(WorkspaceSettingsModel.workspace_id == workspace_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add(self, row: WorkspaceSettingsModel) -> WorkspaceSettingsModel:
        self.session.add(row)
        await self.session.flush()
        return row


class TenantAuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(
        self,
        *,
        event_type: str,
        message: str,
        actor_user_id: uuid.UUID | None = None,
        organization_id: uuid.UUID | None = None,
        workspace_id: uuid.UUID | None = None,
        metadata: dict | None = None,
    ) -> None:
        self.session.add(
            TenantAuditModel(
                event_type=event_type,
                message=message,
                actor_user_id=actor_user_id,
                organization_id=organization_id,
                workspace_id=workspace_id,
                metadata_json=metadata,
            )
        )
        await self.session.flush()
