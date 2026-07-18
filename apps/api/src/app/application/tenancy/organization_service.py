"""Organization application service."""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.identity.authorization import Principal
from app.application.tenancy.tenant_access import TenantAccessService
from app.domain.tenancy.enums import MembershipStatus, OrganizationStatus, WorkspaceRole, WorkspaceStatus
from app.infrastructure.persistence.models.tenancy import (
    OrganizationModel,
    OrganizationSettingsModel,
    WorkspaceMembershipModel,
    WorkspaceModel,
    WorkspaceSettingsModel,
)
from app.infrastructure.persistence.repositories.tenancy import (
    MembershipRepository,
    OrganizationRepository,
    OrgSettingsRepository,
    TenantAuditRepository,
    WorkspaceRepository,
    WorkspaceSettingsRepository,
)
from app.shared.exceptions import ConflictError, NotFoundError, ValidationAppError


def _slugify(value: str) -> str:
    s = value.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    if len(s) < 2:
        raise ValidationAppError("Slug too short", details=[{"field": "slug", "issue": "too_short"}])
    if len(s) > 100:
        s = s[:100].rstrip("-")
    return s


class OrganizationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.orgs = OrganizationRepository(session)
        self.workspaces = WorkspaceRepository(session)
        self.memberships = MembershipRepository(session)
        self.org_settings = OrgSettingsRepository(session)
        self.ws_settings = WorkspaceSettingsRepository(session)
        self.audit = TenantAuditRepository(session)
        self.access = TenantAccessService(session)

    async def create(
        self,
        principal: Principal,
        *,
        name: str,
        slug: str | None = None,
        timezone: str = "UTC",
        currency: str = "USD",
        language: str = "en",
        default_workspace_name: str = "Default",
    ) -> OrganizationModel:
        name = name.strip()
        if len(name) < 2:
            raise ValidationAppError("Organization name too short", details=[{"field": "name", "issue": "too_short"}])
        slug = _slugify(slug or name)
        if await self.orgs.get_by_slug(slug):
            raise ConflictError("Organization slug already exists", code="ORG_SLUG_TAKEN")

        org = OrganizationModel(
            name=name,
            slug=slug,
            status=OrganizationStatus.ACTIVE,
            timezone=timezone,
            currency=currency.upper(),
            language=language,
            owner_user_id=principal.user_id,
            preferences={},
        )
        await self.orgs.add(org)
        await self.org_settings.add(
            OrganizationSettingsModel(
                organization_id=org.id,
                general={"name": name},
                security={"require_mfa": False},
                notifications={},
                branding={},
                regional={"timezone": timezone, "currency": currency, "language": language},
                business_rules={},
            )
        )

        ws_slug = "default"
        ws = WorkspaceModel(
            organization_id=org.id,
            name=default_workspace_name,
            slug=ws_slug,
            status=WorkspaceStatus.ACTIVE,
            timezone=timezone,
            currency=currency.upper(),
            language=language,
            is_default=True,
            metadata_json={},
        )
        await self.workspaces.add(ws)
        await self.ws_settings.add(
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
            event_type="organization.created",
            message=f"Organization '{name}' created",
            actor_user_id=principal.user_id,
            organization_id=org.id,
            workspace_id=ws.id,
            metadata={"slug": slug},
        )
        await self.session.flush()
        return org

    async def get(self, principal: Principal, organization_id: uuid.UUID) -> OrganizationModel:
        await self.access.require_org_access(principal, organization_id)
        org = await self.orgs.get_by_id(organization_id)
        if org is None:
            raise NotFoundError("Organization not found", code="ORG_NOT_FOUND")
        return org

    async def list_mine(self, principal: Principal) -> list[OrganizationModel]:
        if principal.is_superuser:
            # superuser: orgs they own + member of (same query)
            pass
        owned = await self.orgs.list_for_owner(principal.user_id)
        member = await self.orgs.list_for_user(principal.user_id)
        by_id = {o.id: o for o in owned}
        for o in member:
            by_id[o.id] = o
        return list(by_id.values())

    async def update(
        self,
        principal: Principal,
        organization_id: uuid.UUID,
        *,
        name: str | None = None,
        logo_url: str | None = None,
        website: str | None = None,
        timezone: str | None = None,
        currency: str | None = None,
        language: str | None = None,
        status: str | None = None,
        preferences: dict | None = None,
    ) -> OrganizationModel:
        await self.access.require_org_owner(principal, organization_id)
        org = await self.orgs.get_by_id(organization_id)
        if org is None:
            raise NotFoundError("Organization not found", code="ORG_NOT_FOUND")
        if name is not None:
            org.name = name.strip()
        if logo_url is not None:
            org.logo_url = logo_url
        if website is not None:
            org.website = website
        if timezone is not None:
            org.timezone = timezone
        if currency is not None:
            org.currency = currency.upper()
        if language is not None:
            org.language = language
        if status is not None:
            if status not in {s.value for s in OrganizationStatus}:
                raise ValidationAppError("Invalid status", details=[{"field": "status", "issue": "invalid"}])
            org.status = status
        if preferences is not None:
            org.preferences = preferences
        await self.audit.add(
            event_type="organization.updated",
            message="Organization updated",
            actor_user_id=principal.user_id,
            organization_id=org.id,
        )
        await self.session.flush()
        return org

    async def soft_delete(self, principal: Principal, organization_id: uuid.UUID) -> None:
        await self.access.require_org_owner(principal, organization_id)
        org = await self.orgs.get_by_id(organization_id)
        if org is None:
            raise NotFoundError("Organization not found", code="ORG_NOT_FOUND")
        org.soft_delete()
        org.status = OrganizationStatus.ARCHIVED
        for ws in await self.workspaces.list_for_org(organization_id):
            ws.soft_delete()
            ws.status = WorkspaceStatus.ARCHIVED
        await self.audit.add(
            event_type="organization.deleted",
            message="Organization soft-deleted",
            actor_user_id=principal.user_id,
            organization_id=organization_id,
        )
        await self.session.flush()

    async def get_settings(self, principal: Principal, organization_id: uuid.UUID) -> OrganizationSettingsModel:
        await self.access.require_org_access(principal, organization_id)
        settings = await self.org_settings.get(organization_id)
        if settings is None:
            settings = await self.org_settings.add(
                OrganizationSettingsModel(organization_id=organization_id)
            )
        return settings

    async def update_settings(
        self,
        principal: Principal,
        organization_id: uuid.UUID,
        **sections: dict | None,
    ) -> OrganizationSettingsModel:
        await self.access.require_org_owner(principal, organization_id)
        settings = await self.get_settings(principal, organization_id)
        for key in ("general", "security", "notifications", "branding", "regional", "business_rules"):
            if key in sections and sections[key] is not None:
                setattr(settings, key, sections[key])
        await self.audit.add(
            event_type="organization.settings_updated",
            message="Organization settings updated",
            actor_user_id=principal.user_id,
            organization_id=organization_id,
        )
        await self.session.flush()
        return settings
