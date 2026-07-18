"""Workspace, membership, invitation REST API."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.application.identity.authorization import Principal
from app.application.tenancy.invitation_service import InvitationService
from app.application.tenancy.membership_service import MembershipService
from app.application.tenancy.tenant_access import TenantAccessService
from app.application.tenancy.workspace_service import WorkspaceService
from app.presentation.api.deps.auth import get_current_principal
from app.presentation.api.deps.tenancy import (
    get_invitation_service,
    get_membership_service,
    get_tenant_access,
    get_workspace_service,
    resolve_active_tenant,
)
from app.presentation.schemas.identity.auth import MessageResponse
from app.presentation.schemas.tenancy.schemas import (
    InviteCreate,
    InviteResponse,
    InviteTokenRequest,
    MembershipResponse,
    MembershipRoleUpdate,
    TenantContextResponse,
    TransferOwnershipRequest,
    WorkspaceCreate,
    WorkspaceResponse,
    WorkspaceSettingsResponse,
    WorkspaceSettingsUpdate,
    WorkspaceUpdate,
)
from app.shared.types.context import TenantContext

router = APIRouter(tags=["workspaces"])


@router.post(
    "/organizations/{organization_id}/workspaces",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_workspace(
    organization_id: UUID,
    body: WorkspaceCreate,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[WorkspaceService, Depends(get_workspace_service)],
) -> WorkspaceResponse:
    ws = await svc.create(principal, organization_id, **body.model_dump(exclude_unset=True))
    return WorkspaceResponse.model_validate(ws)


@router.get("/organizations/{organization_id}/workspaces", response_model=list[WorkspaceResponse])
async def list_org_workspaces(
    organization_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[WorkspaceService, Depends(get_workspace_service)],
) -> list[WorkspaceResponse]:
    rows = await svc.list_for_org(principal, organization_id)
    return [WorkspaceResponse.model_validate(w) for w in rows]


@router.get("/workspaces", response_model=list[WorkspaceResponse])
async def list_my_workspaces(
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[WorkspaceService, Depends(get_workspace_service)],
) -> list[WorkspaceResponse]:
    rows = await svc.list_mine(principal)
    return [WorkspaceResponse.model_validate(w) for w in rows]


@router.get("/workspaces/current", response_model=TenantContextResponse)
async def current_workspace_context(
    principal: Annotated[Principal, Depends(get_current_principal)],
    tenant: Annotated[TenantContext, Depends(resolve_active_tenant)],
    access: Annotated[TenantAccessService, Depends(get_tenant_access)],
) -> TenantContextResponse:
    role = None
    status_m = None
    if tenant.workspace_id:
        m = await access.memberships.get(tenant.workspace_id, principal.user_id)
        if m:
            role = m.role_code
            status_m = m.status
    return TenantContextResponse(
        organization_id=tenant.company_id,
        workspace_id=tenant.workspace_id,
        role_code=role,
        membership_status=status_m,
    )


@router.get("/workspaces/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[WorkspaceService, Depends(get_workspace_service)],
) -> WorkspaceResponse:
    ws = await svc.get(principal, workspace_id)
    return WorkspaceResponse.model_validate(ws)


@router.patch("/workspaces/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: UUID,
    body: WorkspaceUpdate,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[WorkspaceService, Depends(get_workspace_service)],
) -> WorkspaceResponse:
    ws = await svc.update(principal, workspace_id, **body.model_dump(exclude_unset=True))
    return WorkspaceResponse.model_validate(ws)


@router.delete("/workspaces/{workspace_id}", response_model=MessageResponse)
async def delete_workspace(
    workspace_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[WorkspaceService, Depends(get_workspace_service)],
) -> MessageResponse:
    await svc.soft_delete(principal, workspace_id)
    return MessageResponse(message="Workspace archived")


@router.get("/workspaces/{workspace_id}/settings", response_model=WorkspaceSettingsResponse)
async def get_ws_settings(
    workspace_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[WorkspaceService, Depends(get_workspace_service)],
) -> WorkspaceSettingsResponse:
    s = await svc.get_settings(principal, workspace_id)
    return WorkspaceSettingsResponse.model_validate(s)


@router.patch("/workspaces/{workspace_id}/settings", response_model=WorkspaceSettingsResponse)
async def update_ws_settings(
    workspace_id: UUID,
    body: WorkspaceSettingsUpdate,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[WorkspaceService, Depends(get_workspace_service)],
) -> WorkspaceSettingsResponse:
    s = await svc.update_settings(principal, workspace_id, **body.model_dump(exclude_unset=True))
    return WorkspaceSettingsResponse.model_validate(s)


@router.get("/workspaces/{workspace_id}/members", response_model=list[MembershipResponse])
async def list_members(
    workspace_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[MembershipService, Depends(get_membership_service)],
) -> list[MembershipResponse]:
    rows = await svc.list_members(principal, workspace_id)
    return [MembershipResponse.model_validate(m) for m in rows]


@router.patch("/workspaces/{workspace_id}/members/{user_id}", response_model=MembershipResponse)
async def update_member_role(
    workspace_id: UUID,
    user_id: UUID,
    body: MembershipRoleUpdate,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[MembershipService, Depends(get_membership_service)],
) -> MembershipResponse:
    m = await svc.update_role(principal, workspace_id, user_id, body.role_code)
    return MembershipResponse.model_validate(m)


@router.post("/workspaces/{workspace_id}/members/{user_id}/suspend", response_model=MembershipResponse)
async def suspend_member(
    workspace_id: UUID,
    user_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[MembershipService, Depends(get_membership_service)],
) -> MembershipResponse:
    m = await svc.suspend(principal, workspace_id, user_id)
    return MembershipResponse.model_validate(m)


@router.delete("/workspaces/{workspace_id}/members/{user_id}", response_model=MessageResponse)
async def remove_member(
    workspace_id: UUID,
    user_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[MembershipService, Depends(get_membership_service)],
) -> MessageResponse:
    await svc.remove(principal, workspace_id, user_id)
    return MessageResponse(message="Member removed")


@router.post("/workspaces/{workspace_id}/transfer-ownership", response_model=MembershipResponse)
async def transfer_ownership(
    workspace_id: UUID,
    body: TransferOwnershipRequest,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[MembershipService, Depends(get_membership_service)],
) -> MembershipResponse:
    m = await svc.transfer_ownership(principal, workspace_id, body.new_owner_user_id)
    return MembershipResponse.model_validate(m)


@router.post(
    "/workspaces/{workspace_id}/invitations",
    response_model=InviteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def invite_member(
    workspace_id: UUID,
    body: InviteCreate,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[InvitationService, Depends(get_invitation_service)],
) -> InviteResponse:
    inv, raw = await svc.invite(
        principal,
        workspace_id,
        email=str(body.email),
        role_code=body.role_code,
        message=body.message,
        expires_days=body.expires_days,
    )
    data = InviteResponse.model_validate(inv)
    return data.model_copy(update={"token": raw})


@router.get("/workspaces/{workspace_id}/invitations", response_model=list[InviteResponse])
async def list_invitations(
    workspace_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[InvitationService, Depends(get_invitation_service)],
) -> list[InviteResponse]:
    rows = await svc.list_pending(principal, workspace_id)
    return [InviteResponse.model_validate(i) for i in rows]


@router.post("/invitations/accept", response_model=MembershipResponse)
async def accept_invitation(
    body: InviteTokenRequest,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[InvitationService, Depends(get_invitation_service)],
) -> MembershipResponse:
    m = await svc.accept(principal, token=body.token)
    return MembershipResponse.model_validate(m)


@router.post("/invitations/reject", response_model=MessageResponse)
async def reject_invitation(
    body: InviteTokenRequest,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[InvitationService, Depends(get_invitation_service)],
) -> MessageResponse:
    await svc.reject(principal, token=body.token)
    return MessageResponse(message="Invitation rejected")


@router.delete("/invitations/{invitation_id}", response_model=MessageResponse)
async def revoke_invitation(
    invitation_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[InvitationService, Depends(get_invitation_service)],
) -> MessageResponse:
    await svc.revoke(principal, invitation_id)
    return MessageResponse(message="Invitation revoked")
