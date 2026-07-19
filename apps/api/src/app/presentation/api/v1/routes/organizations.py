"""Organization REST API."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.application.identity.authorization import Principal
from app.application.tenancy.organization_service import OrganizationService
from app.presentation.api.deps.auth import get_current_principal
from app.presentation.api.deps.tenancy import get_organization_service
from app.presentation.schemas.tenancy.schemas import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
    OrgSettingsResponse,
    OrgSettingsUpdate,
)
from app.presentation.schemas.identity.auth import MessageResponse

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    body: OrganizationCreate,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[OrganizationService, Depends(get_organization_service)],
) -> OrganizationResponse:
    org = await svc.create(
        principal,
        name=body.name,
        slug=body.slug,
        timezone=body.timezone,
        currency=body.currency,
        language=body.language,
        default_workspace_name=body.default_workspace_name,
    )
    return OrganizationResponse.model_validate(org)


@router.get("", response_model=list[OrganizationResponse])
async def list_organizations(
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[OrganizationService, Depends(get_organization_service)],
) -> list[OrganizationResponse]:
    orgs = await svc.list_mine(principal)
    return [OrganizationResponse.model_validate(o) for o in orgs]


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[OrganizationService, Depends(get_organization_service)],
) -> OrganizationResponse:
    org = await svc.get(principal, organization_id)
    return OrganizationResponse.model_validate(org)


@router.patch("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: UUID,
    body: OrganizationUpdate,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[OrganizationService, Depends(get_organization_service)],
) -> OrganizationResponse:
    org = await svc.update(principal, organization_id, **body.model_dump(exclude_unset=True))
    return OrganizationResponse.model_validate(org)


@router.delete("/{organization_id}", response_model=MessageResponse)
async def delete_organization(
    organization_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[OrganizationService, Depends(get_organization_service)],
) -> MessageResponse:
    await svc.soft_delete(principal, organization_id)
    return MessageResponse(message="Organization archived")


@router.get("/{organization_id}/settings", response_model=OrgSettingsResponse)
async def get_org_settings(
    organization_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[OrganizationService, Depends(get_organization_service)],
) -> OrgSettingsResponse:
    s = await svc.get_settings(principal, organization_id)
    return OrgSettingsResponse.model_validate(s)


@router.patch("/{organization_id}/settings", response_model=OrgSettingsResponse)
async def update_org_settings(
    organization_id: UUID,
    body: OrgSettingsUpdate,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[OrganizationService, Depends(get_organization_service)],
) -> OrgSettingsResponse:
    s = await svc.update_settings(principal, organization_id, **body.model_dump(exclude_unset=True))
    return OrgSettingsResponse.model_validate(s)
