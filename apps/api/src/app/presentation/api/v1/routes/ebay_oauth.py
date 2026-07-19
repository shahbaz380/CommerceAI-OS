"""eBay-specific OAuth account connection routes (Prompt 18)."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.identity.authorization import Principal
from app.application.marketplaces.connection_service import MarketplaceConnectionService
from app.application.marketplaces.credential_service import MarketplaceCredentialService
from app.domain.marketplaces.enums import MarketplaceChannel
from app.presentation.api.deps.auth import get_current_principal
from app.presentation.api.deps.common import get_db_session
from app.presentation.schemas.identity.auth import MessageResponse
from app.presentation.schemas.marketplaces.schemas import (
    ConnectCallbackResponse,
    ConnectStartResponse,
    ConnectionHealthResponse,
    ConnectionResponse,
    CredentialCreate,
    CredentialResponse,
)
from app.shared.exceptions import ValidationAppError
from pydantic import BaseModel, Field

router = APIRouter(prefix="/marketplaces/ebay", tags=["ebay-oauth"])


class EbayConnectQuery(BaseModel):
    environment: str = Field(default="sandbox", pattern="^(sandbox|production)$")
    display_name: str | None = None
    alias: str | None = None
    connection_id: UUID | None = None


class EbayCallbackBody(BaseModel):
    code: str | None = None
    state: str
    connection_id: UUID | None = None
    error: str | None = None
    error_description: str | None = None


class EbayRefreshBody(BaseModel):
    force: bool = False


class EbayReconnectBody(BaseModel):
    environment: str | None = Field(default=None, pattern="^(sandbox|production)$")


async def _svc(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MarketplaceConnectionService:
    return MarketplaceConnectionService(session)


async def _creds(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MarketplaceCredentialService:
    return MarketplaceCredentialService(session)


def _ws_header(x_workspace_id: str | None) -> UUID:
    if not x_workspace_id:
        raise ValidationAppError(
            "X-Workspace-Id header is required",
            details=[{"field": "X-Workspace-Id", "issue": "required"}],
        )
    try:
        return UUID(x_workspace_id)
    except ValueError as exc:
        raise ValidationAppError(
            "Invalid workspace id",
            details=[{"field": "X-Workspace-Id", "issue": "invalid_uuid"}],
        ) from exc


@router.post(
    "/workspaces/{workspace_id}/credentials",
    response_model=CredentialResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upsert_ebay_credentials(
    workspace_id: UUID,
    body: CredentialCreate,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[MarketplaceCredentialService, Depends(_creds)],
) -> CredentialResponse:
    row = await svc.upsert(
        principal,
        workspace_id,
        channel=MarketplaceChannel.EBAY.value,
        environment=body.environment,
        client_id=body.client_id,
        client_secret=body.client_secret,
        redirect_uri=body.redirect_uri,
        scopes=body.scopes,
        ru_name=body.ru_name,
        label=body.label,
    )
    return CredentialResponse.model_validate(row)


@router.get(
    "/workspaces/{workspace_id}/connect",
    response_model=ConnectStartResponse,
)
async def ebay_connect_for_workspace(
    workspace_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[MarketplaceConnectionService, Depends(_svc)],
    environment: str = Query(default="sandbox", pattern="^(sandbox|production)$"),
    display_name: str | None = None,
    alias: str | None = None,
    connection_id: UUID | None = None,
) -> ConnectStartResponse:
    result = await svc.begin_connect(
        principal,
        workspace_id,
        channel=MarketplaceChannel.EBAY.value,
        environment=environment,
        display_name=display_name,
        alias=alias,
        connection_id=connection_id,
    )
    return ConnectStartResponse.model_validate(result)


@router.get("/callback", response_model=ConnectCallbackResponse)
async def ebay_callback_get(
    request: Request,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[MarketplaceConnectionService, Depends(_svc)],
    state: str = Query(...),
    code: str | None = Query(default=None),
    error: str | None = Query(default=None),
    error_description: str | None = Query(default=None),
    workspace_id: UUID | None = Query(default=None),
    connection_id: UUID | None = Query(default=None),
    x_workspace_id: Annotated[str | None, Query(alias="X-Workspace-Id")] = None,
) -> ConnectCallbackResponse:
    """Browser redirect callback (GET). workspace_id required via query if not recoverable from state."""
    # workspace comes from query for authenticated SPA completion
    ws = workspace_id
    if ws is None and x_workspace_id:
        ws = UUID(x_workspace_id)
    if ws is None:
        raise ValidationAppError(
            "workspace_id query parameter is required for callback completion",
            details=[{"field": "workspace_id", "issue": "required"}],
        )
    result = await svc.complete_connect(
        principal,
        ws,
        channel=MarketplaceChannel.EBAY.value,
        code=code or "",
        state=state,
        connection_id=connection_id,
        oauth_error=error,
        oauth_error_description=error_description,
    )
    return ConnectCallbackResponse.model_validate(result)


@router.post(
    "/workspaces/{workspace_id}/callback",
    response_model=ConnectCallbackResponse,
)
async def ebay_callback_post(
    workspace_id: UUID,
    body: EbayCallbackBody,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[MarketplaceConnectionService, Depends(_svc)],
) -> ConnectCallbackResponse:
    result = await svc.complete_connect(
        principal,
        workspace_id,
        channel=MarketplaceChannel.EBAY.value,
        code=body.code or "",
        state=body.state,
        connection_id=body.connection_id,
        oauth_error=body.error,
        oauth_error_description=body.error_description,
    )
    return ConnectCallbackResponse.model_validate(result)


@router.post("/workspaces/{workspace_id}/accounts/{connection_id}/refresh")
async def ebay_refresh(
    workspace_id: UUID,
    connection_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[MarketplaceConnectionService, Depends(_svc)],
    body: EbayRefreshBody | None = None,
) -> dict[str, Any]:
    force = body.force if body else False
    return await svc.refresh(principal, workspace_id, connection_id, force=force)


@router.post(
    "/workspaces/{workspace_id}/accounts/{connection_id}/disconnect",
    response_model=MessageResponse,
)
async def ebay_disconnect(
    workspace_id: UUID,
    connection_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[MarketplaceConnectionService, Depends(_svc)],
) -> MessageResponse:
    await svc.disconnect(principal, workspace_id, connection_id)
    return MessageResponse(message="eBay account disconnected")


@router.post(
    "/workspaces/{workspace_id}/accounts/{connection_id}/reconnect",
    response_model=ConnectStartResponse,
)
async def ebay_reconnect(
    workspace_id: UUID,
    connection_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[MarketplaceConnectionService, Depends(_svc)],
    body: EbayReconnectBody | None = None,
) -> ConnectStartResponse:
    result = await svc.reconnect(
        principal,
        workspace_id,
        connection_id,
        environment=body.environment if body else None,
    )
    return ConnectStartResponse.model_validate(result)


@router.get("/workspaces/{workspace_id}/status")
async def ebay_status(
    workspace_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[MarketplaceConnectionService, Depends(_svc)],
) -> dict[str, Any]:
    rows = await svc.list_connections(
        principal, workspace_id, channel=MarketplaceChannel.EBAY.value
    )
    connected = [r for r in rows if r.status == "connected"]
    default = next((r for r in rows if r.is_default), None)
    return {
        "workspace_id": str(workspace_id),
        "channel": "ebay",
        "total_accounts": len(rows),
        "connected_accounts": len(connected),
        "default_connection_id": str(default.id) if default else None,
        "statuses": {r.status: sum(1 for x in rows if x.status == r.status) for r in rows},
        "accounts": [
            {
                "id": str(r.id),
                "status": r.status,
                "environment": r.environment,
                "display_name": r.display_name,
                "alias": r.alias,
                "is_default": r.is_default,
                "external_username": r.external_username,
            }
            for r in rows
        ],
    }


@router.get(
    "/workspaces/{workspace_id}/accounts",
    response_model=list[ConnectionResponse],
)
async def ebay_accounts(
    workspace_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[MarketplaceConnectionService, Depends(_svc)],
) -> list[ConnectionResponse]:
    rows = await svc.list_connections(
        principal, workspace_id, channel=MarketplaceChannel.EBAY.value
    )
    return [ConnectionResponse.model_validate(r) for r in rows]


@router.get(
    "/workspaces/{workspace_id}/accounts/{connection_id}",
    response_model=ConnectionResponse,
)
async def ebay_account_detail(
    workspace_id: UUID,
    connection_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[MarketplaceConnectionService, Depends(_svc)],
) -> ConnectionResponse:
    row = await svc.get_connection(principal, workspace_id, connection_id)
    if row.channel != MarketplaceChannel.EBAY.value:
        raise ValidationAppError("Not an eBay connection")
    return ConnectionResponse.model_validate(row)


@router.patch(
    "/workspaces/{workspace_id}/accounts/{connection_id}/default",
    response_model=ConnectionResponse,
)
async def ebay_set_default(
    workspace_id: UUID,
    connection_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[MarketplaceConnectionService, Depends(_svc)],
) -> ConnectionResponse:
    row = await svc.set_default(principal, workspace_id, connection_id)
    return ConnectionResponse.model_validate(row)


@router.delete(
    "/workspaces/{workspace_id}/accounts/{connection_id}",
    response_model=MessageResponse,
)
async def ebay_delete_account(
    workspace_id: UUID,
    connection_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[MarketplaceConnectionService, Depends(_svc)],
) -> MessageResponse:
    await svc.disconnect(principal, workspace_id, connection_id)
    # soft-delete connection row
    conn = await svc.connections.get_for_workspace(workspace_id, connection_id)
    if conn:
        conn.soft_delete()
        conn.status = "deactivated"
        await svc.session.flush()
    return MessageResponse(message="eBay account removed")


@router.get(
    "/workspaces/{workspace_id}/accounts/{connection_id}/health",
    response_model=ConnectionHealthResponse,
)
async def ebay_health(
    workspace_id: UUID,
    connection_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[MarketplaceConnectionService, Depends(_svc)],
) -> ConnectionHealthResponse:
    data = await svc.health(principal, workspace_id, connection_id)
    return ConnectionHealthResponse.model_validate(data)


@router.post(
    "/workspaces/{workspace_id}/accounts/{connection_id}/validate",
)
async def ebay_validate(
    workspace_id: UUID,
    connection_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[MarketplaceConnectionService, Depends(_svc)],
) -> dict[str, Any]:
    return await svc.validate(principal, workspace_id, connection_id)


@router.post(
    "/workspaces/{workspace_id}/accounts/{connection_id}/suspend",
    response_model=ConnectionResponse,
)
async def ebay_suspend(
    workspace_id: UUID,
    connection_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[MarketplaceConnectionService, Depends(_svc)],
) -> ConnectionResponse:
    row = await svc.suspend(principal, workspace_id, connection_id)
    return ConnectionResponse.model_validate(row)


@router.post(
    "/workspaces/{workspace_id}/accounts/{connection_id}/resume",
    response_model=ConnectionResponse,
)
async def ebay_resume(
    workspace_id: UUID,
    connection_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[MarketplaceConnectionService, Depends(_svc)],
) -> ConnectionResponse:
    row = await svc.resume(principal, workspace_id, connection_id)
    return ConnectionResponse.model_validate(row)
