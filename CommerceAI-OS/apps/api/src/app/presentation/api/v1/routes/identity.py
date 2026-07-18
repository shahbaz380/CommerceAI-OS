"""Identity catalog routes (roles/permissions) + OAuth foundation."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.identity.authorization import Principal
from app.application.identity.bootstrap import seed_identity_catalog
from app.domain.identity.permissions import PermissionCode
from app.infrastructure.persistence.repositories.identity import PermissionRepository, RoleRepository
from app.infrastructure.security.oauth import get_oauth_registry
from app.presentation.api.deps.auth import get_current_principal, require_permission
from app.presentation.api.deps.common import get_db_session
from app.presentation.schemas.identity.auth import MessageResponse, PermissionResponse, RoleResponse
from app.shared.utils.ids import new_request_id

router = APIRouter(prefix="/identity", tags=["identity"])


@router.post("/seed", response_model=MessageResponse)
async def seed_catalog(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[Principal, Depends(require_permission(PermissionCode.PLATFORM_ADMIN.value))],
) -> MessageResponse:
    stats = await seed_identity_catalog(session)
    return MessageResponse(message="Identity catalog seeded", details=stats)


@router.get("/roles", response_model=list[RoleResponse])
async def list_roles(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[Principal, Depends(get_current_principal)],
) -> list[RoleResponse]:
    await seed_identity_catalog(session)
    roles = await RoleRepository(session).list_all()
    return [
        RoleResponse(
            code=r.code,
            name=r.name,
            hierarchy_rank=r.hierarchy_rank,
            is_system=r.is_system,
        )
        for r in roles
    ]


@router.get("/permissions", response_model=list[PermissionResponse])
async def list_permissions(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[Principal, Depends(get_current_principal)],
) -> list[PermissionResponse]:
    await seed_identity_catalog(session)
    perms = await PermissionRepository(session).list_all()
    return [
        PermissionResponse(code=p.code, module=p.module, description=p.description) for p in perms
    ]


@router.get("/oauth/providers")
async def oauth_providers(
    _: Annotated[Principal, Depends(get_current_principal)],
) -> dict:
    registry = get_oauth_registry()
    return {"providers": registry.list_providers(), "status": "framework_only"}


@router.get("/oauth/{provider}/authorize")
async def oauth_authorize_placeholder(
    provider: str,
    _: Annotated[Principal, Depends(get_current_principal)],
) -> dict:
    """Return structural authorize URL — no real OAuth yet."""
    client = get_oauth_registry().get(provider)
    state = new_request_id()
    req = client.build_authorize_url(state=state, redirect_uri="https://app.local/oauth/callback")
    return {
        "provider": req.provider.value,
        "authorization_url": req.authorization_url,
        "state": req.state,
        "implemented": False,
    }
