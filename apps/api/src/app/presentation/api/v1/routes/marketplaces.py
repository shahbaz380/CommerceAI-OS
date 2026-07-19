"""Marketplace integration REST API — connections, credentials, OAuth, webhooks foundation."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request, status

from app.application.identity.authorization import Principal
from app.application.marketplaces.connection_service import MarketplaceConnectionService
from app.application.marketplaces.credential_service import MarketplaceCredentialService
from app.application.tenancy.tenant_access import TenantAccessService
from app.domain.tenancy.enums import WorkspaceRole
from app.infrastructure.marketplace.webhooks.receiver import WebhookReceiver
from app.presentation.api.deps.auth import get_current_principal
from app.presentation.api.deps.common import get_db_session
from app.presentation.api.deps.tenancy import get_tenant_access
from app.presentation.schemas.identity.auth import MessageResponse
from app.presentation.schemas.marketplaces.schemas import (
    ConnectCallbackRequest,
    ConnectCallbackResponse,
    ConnectStartRequest,
    ConnectStartResponse,
    ConnectionHealthResponse,
    ConnectionResponse,
    CredentialCreate,
    CredentialResponse,
    MarketplaceChannelInfo,
    WebhookReceiveResponse,
)
from app.shared.exceptions import ValidationAppError
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/marketplaces", tags=["marketplaces"])


async def _connection_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MarketplaceConnectionService:
    return MarketplaceConnectionService(session)


async def _credential_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MarketplaceCredentialService:
    return MarketplaceCredentialService(session)


@router.get("/channels", response_model=list[MarketplaceChannelInfo])
async def list_channels(
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[MarketplaceConnectionService, Depends(_connection_service)],
) -> list[MarketplaceChannelInfo]:
    rows = await svc.list_channels()
    return [MarketplaceChannelInfo.model_validate(r) for r in rows]


@router.post(
    "/workspaces/{workspace_id}/credentials",
    response_model=CredentialResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upsert_credentials(
    workspace_id: UUID,
    body: CredentialCreate,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[MarketplaceCredentialService, Depends(_credential_service)],
) -> CredentialResponse:
    row = await svc.upsert(
        principal,
        workspace_id,
        channel=body.channel,
        environment=body.environment,
        client_id=body.client_id,
        client_secret=body.client_secret,
        redirect_uri=body.redirect_uri,
        scopes=body.scopes,
        ru_name=body.ru_name,
        label=body.label,
    )
    return CredentialResponse.model_validate(row)


@router.get("/workspaces/{workspace_id}/credentials", response_model=list[CredentialResponse])
async def list_credentials(
    workspace_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[MarketplaceCredentialService, Depends(_credential_service)],
) -> list[CredentialResponse]:
    rows = await svc.list(principal, workspace_id)
    return [CredentialResponse.model_validate(r) for r in rows]


@router.get("/workspaces/{workspace_id}/connections", response_model=list[ConnectionResponse])
async def list_connections(
    workspace_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[MarketplaceConnectionService, Depends(_connection_service)],
    channel: str | None = None,
) -> list[ConnectionResponse]:
    rows = await svc.list_connections(principal, workspace_id, channel=channel)
    return [ConnectionResponse.model_validate(r) for r in rows]


@router.get(
    "/workspaces/{workspace_id}/connections/{connection_id}",
    response_model=ConnectionResponse,
)
async def get_connection(
    workspace_id: UUID,
    connection_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[MarketplaceConnectionService, Depends(_connection_service)],
) -> ConnectionResponse:
    row = await svc.get_connection(principal, workspace_id, connection_id)
    return ConnectionResponse.model_validate(row)


@router.post(
    "/workspaces/{workspace_id}/connect",
    response_model=ConnectStartResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_connect(
    workspace_id: UUID,
    body: ConnectStartRequest,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[MarketplaceConnectionService, Depends(_connection_service)],
) -> ConnectStartResponse:
    result = await svc.begin_connect(
        principal,
        workspace_id,
        channel=body.channel,
        environment=body.environment,
        display_name=body.display_name,
    )
    return ConnectStartResponse.model_validate(result)


@router.post(
    "/workspaces/{workspace_id}/connect/callback",
    response_model=ConnectCallbackResponse,
)
async def connect_callback(
    workspace_id: UUID,
    body: ConnectCallbackRequest,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[MarketplaceConnectionService, Depends(_connection_service)],
) -> ConnectCallbackResponse:
    result = await svc.complete_connect(
        principal,
        workspace_id,
        channel=body.channel,
        code=body.code,
        state=body.state,
        connection_id=body.connection_id,
    )
    return ConnectCallbackResponse.model_validate(result)


@router.post(
    "/workspaces/{workspace_id}/connections/{connection_id}/disconnect",
    response_model=MessageResponse,
)
async def disconnect(
    workspace_id: UUID,
    connection_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[MarketplaceConnectionService, Depends(_connection_service)],
) -> MessageResponse:
    await svc.disconnect(principal, workspace_id, connection_id)
    return MessageResponse(message="Marketplace disconnected")


@router.post(
    "/workspaces/{workspace_id}/connections/{connection_id}/refresh",
)
async def refresh_token(
    workspace_id: UUID,
    connection_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[MarketplaceConnectionService, Depends(_connection_service)],
) -> dict[str, Any]:
    return await svc.refresh(principal, workspace_id, connection_id)


@router.get(
    "/workspaces/{workspace_id}/connections/{connection_id}/validate",
)
async def validate_connection(
    workspace_id: UUID,
    connection_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[MarketplaceConnectionService, Depends(_connection_service)],
) -> dict[str, Any]:
    return await svc.validate(principal, workspace_id, connection_id)


@router.get(
    "/workspaces/{workspace_id}/connections/{connection_id}/health",
    response_model=ConnectionHealthResponse,
)
async def connection_health(
    workspace_id: UUID,
    connection_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[MarketplaceConnectionService, Depends(_connection_service)],
) -> ConnectionHealthResponse:
    data = await svc.health(principal, workspace_id, connection_id)
    return ConnectionHealthResponse.model_validate(data)


@router.post(
    "/webhooks/{channel}",
    response_model=WebhookReceiveResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def receive_webhook(
    channel: str,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    x_marketplace_webhook_secret: Annotated[str | None, Header()] = None,
) -> WebhookReceiveResponse:
    """Public webhook receiver foundation — no business processing."""
    if not channel or len(channel) > 32:
        raise ValidationAppError("Invalid channel")
    raw = await request.body()
    payload: dict[str, Any] | None
    try:
        payload = await request.json()
    except Exception:
        payload = {"raw_text": raw.decode("utf-8", errors="replace")[:4000]}
    headers = {k: v for k, v in request.headers.items()}
    receiver = WebhookReceiver(session)
    row = await receiver.receive(
        channel=channel,
        headers=headers,
        payload=payload if isinstance(payload, dict) else {"data": payload},
        secret=x_marketplace_webhook_secret,
        raw_body=raw,
    )
    return WebhookReceiveResponse(
        id=row.id,
        channel=row.channel,
        processed=row.processed,
        signature_valid=row.signature_valid,
    )
