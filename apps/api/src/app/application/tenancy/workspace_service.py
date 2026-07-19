"""Workspace application service."""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.identity.authorization import Principal
from app.application.tenancy.tenant_access import TenantAccessService
from app.domain.tenancy.enums import MembershipStatus, WorkspaceRole, WorkspaceStatus
from app.infrastructure.persistence.models.tenancy import (
    WorkspaceMembershipModel,
    WorkspaceModel,
    WorkspaceSettingsModel,
)
from app.infrastructure.persistence.repositories.tenancy import (
    MembershipRepository,
    TenantAuditRepository,
    WorkspaceRepository,
    WorkspaceSettingsRepository,
)
from app.shared.exceptions import ConflictError, NotFoundError, ValidationAppError


def _slugify(value: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    if len(s) < 2:
        raise ValidationAppError("Slug too short", details=[{"field": "slug", "issue": "too_short"}])
    return s[:100]


class WorkspaceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.workspaces = WorkspaceRepository(session)
        self.memberships = MembershipRepository(session)
        self.settings_repo = WorkspaceSettingsRepository(session)
        self.audit = TenantAuditRepository(session)
        self.access = TenantAccessService(session)

    async def create(
        self,
        principal: Principal,
        organization_id: uuid.UUID,
        *,
        name: str,
        slug: str | None = None,
        description: str | None = None,
        timezone: str | None = None,
        currency: str | None = None,
        language: str | None = None,
    ) -> WorkspaceModel:
        await self.access.require_org_owner(principal, organization_id)
        name = name.strip()
        slug = _slugify(slug or name)
        if await self.workspaces.get_by_org_slug(organization_id, slug):
            raise ConflictError("Workspace slug exists in organization", code="WORKSPACE_SLUG_TAKEN")

        ws = WorkspaceModel(
            organization_id=organization_id,
            name=name,
            slug=slug,
            status=WorkspaceStatus.ACTIVE,
            description=description,
            timezone=timezone,
            currency=currency.upper() if currency else None,
            language=language,
            metadata_json={},
            is_default=False,
        )
        await self.workspaces.add(ws)
        await self.settings_repo.add(
            WorkspaceSettingsModel(
                workspace_id=ws.id,
                preferences={},
                marketplace={},
                automation={},
                ai={"ai_writes_enabled": False},
                notifications={},
            )
        )
        await self.memberships.add(
            WorkspaceMembershipModel(
                workspace_id=ws.id,
                user_id=principal.user_id,
                role_code=WorkspaceRole.OWNER,
                status=MembershipStatus.ACTIVE,
                invited_by=principal.user_id,
                joined_at=datetime.now(UTC),
            )
        )
        await self.audit.add(
            event_type="workspace.created",
            message=f"Workspace '{name}' created",
            actor_user_id=principal.user_id,
            organization_id=organization_id,
            workspace_id=ws.id,
        )
        await self.session.flush()
        return ws

    async def get(self, principal: Principal, workspace_id: uuid.UUID) -> WorkspaceModel:
        ws, _ = await self.access.require_workspace_member(principal, workspace_id)
        return ws

    async def list_for_org(self, principal: Principal, organization_id: uuid.UUID) -> list[WorkspaceModel]:
        await self.access.require_org_access(principal, organization_id)
        return await self.workspaces.list_for_org(organization_id)

    async def list_mine(self, principal: Principal) -> list[WorkspaceModel]:
        return await self.workspaces.list_for_user(principal.user_id)

    async def update(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        **fields,
    ) -> WorkspaceModel:
        ws, _ = await self.access.require_workspace_member(
            principal, workspace_id, min_role=WorkspaceRole.MANAGER
        )
        for key in ("name", "description", "timezone", "currency", "language", "status", "metadata_json"):
            if key in fields and fields[key] is not None:
                val = fields[key]
                if key == "currency" and isinstance(val, str):
                    val = val.upper()
                if key == "status" and val not in {s.value for s in WorkspaceStatus}:
                    raise ValidationAppError("Invalid status", details=[{"field": "status", "issue": "invalid"}])
                setattr(ws, key if key != "metadata_json" else "metadata_json", val)
        await self.audit.add(
            event_type="workspace.updated",
            message="Workspace updated",
            actor_user_id=principal.user_id,
            organization_id=ws.organization_id,
            workspace_id=ws.id,
        )
        await self.session.flush()
        return ws

    async def soft_delete(self, principal: Principal, workspace_id: uuid.UUID) -> None:
        ws, _ = await self.access.require_workspace_member(
            principal, workspace_id, min_role=WorkspaceRole.OWNER
        )
        if ws.is_default:
            raise ValidationAppError(
                "Cannot delete default workspace",
                details=[{"field": "workspace", "issue": "is_default"}],
            )
        ws.soft_delete()
        ws.status = WorkspaceStatus.ARCHIVED
        await self.audit.add(
            event_type="workspace.deleted",
            message="Workspace soft-deleted",
            actor_user_id=principal.user_id,
            organization_id=ws.organization_id,
            workspace_id=ws.id,
        )
        await self.session.flush()

    async def get_settings(self, principal: Principal, workspace_id: uuid.UUID) -> WorkspaceSettingsModel:
        await self.access.require_workspace_member(principal, workspace_id)
        settings = await self.settings_repo.get(workspace_id)
        if settings is None:
            settings = await self.settings_repo.add(WorkspaceSettingsModel(workspace_id=workspace_id))
        return settings

    async def update_settings(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        **sections,
    ) -> WorkspaceSettingsModel:
        ws, _ = await self.access.require_workspace_member(
            principal, workspace_id, min_role=WorkspaceRole.MANAGER
        )
        settings = await self.get_settings(principal, workspace_id)
        for key in ("preferences", "marketplace", "automation", "ai", "notifications"):
            if key in sections and sections[key] is not None:
                setattr(settings, key, sections[key])
        await self.audit.add(
            event_type="workspace.settings_updated",
            message="Workspace settings updated",
            actor_user_id=principal.user_id,
            organization_id=ws.organization_id,
            workspace_id=workspace_id,
        )
        await self.session.flush()
        return settings
