"""Internal inventory API routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.identity.authorization import Principal
from app.application.inventory.services import AdjustmentService, InventoryQueryService, InventoryService, ReservationService, StockTransferService, WarehouseService
from app.presentation.api.deps.auth import get_current_principal
from app.presentation.api.deps.common import get_db_session
from app.presentation.schemas.identity.auth import MessageResponse
from app.presentation.schemas.inventory.schemas import (
    AdjustmentRequest,
    InventoryCreate,
    InventoryResponse,
    InventoryUpdate,
    ReservationCreate,
    TransferRequest,
    WarehouseCreate,
    WarehouseResponse,
)
from app.shared.exceptions import ValidationAppError

router = APIRouter(tags=["inventory"])


def _require_workspace(x_workspace_id: str | None) -> UUID:
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


async def _inventory_service(session: Annotated[AsyncSession, Depends(get_db_session)]) -> InventoryService:
    return InventoryService(session)


async def _reservation_service(session: Annotated[AsyncSession, Depends(get_db_session)]) -> ReservationService:
    return ReservationService(session)


async def _warehouse_service(session: Annotated[AsyncSession, Depends(get_db_session)]) -> WarehouseService:
    return WarehouseService(session)


async def _transfer_service(session: Annotated[AsyncSession, Depends(get_db_session)]) -> StockTransferService:
    return StockTransferService(session)


async def _adjustment_service(session: Annotated[AsyncSession, Depends(get_db_session)]) -> AdjustmentService:
    return AdjustmentService(session)


async def _query_service(session: Annotated[AsyncSession, Depends(get_db_session)]) -> InventoryQueryService:
    return InventoryQueryService(session)


@router.post("/inventory", response_model=InventoryResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory(
    body: InventoryCreate,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[InventoryService, Depends(_inventory_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> InventoryResponse:
    workspace_id = _require_workspace(x_workspace_id)
    inventory = await svc.create_inventory(principal, workspace_id, **body.model_dump())
    return InventoryResponse.model_validate(inventory)


@router.get("/inventory", response_model=list[InventoryResponse])
async def list_inventory(
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[InventoryQueryService, Depends(_query_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> list[InventoryResponse]:
    workspace_id = _require_workspace(x_workspace_id)
    rows, _ = await svc.list_inventory(workspace_id, offset=offset, limit=limit)
    return [InventoryResponse.model_validate(r) for r in rows]


@router.get("/inventory/{inventory_id}", response_model=InventoryResponse)
async def get_inventory(
    inventory_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[InventoryService, Depends(_inventory_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> InventoryResponse:
    workspace_id = _require_workspace(x_workspace_id)
    inventory = await svc.get_inventory(principal, workspace_id, inventory_id)
    return InventoryResponse.model_validate(inventory)


@router.patch("/inventory/{inventory_id}", response_model=InventoryResponse)
async def update_inventory(
    inventory_id: UUID,
    body: InventoryUpdate,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[InventoryService, Depends(_inventory_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> InventoryResponse:
    workspace_id = _require_workspace(x_workspace_id)
    inventory = await svc.update_inventory(principal, workspace_id, inventory_id, **body.model_dump(exclude_unset=True))
    return InventoryResponse.model_validate(inventory)


@router.delete("/inventory/{inventory_id}", response_model=MessageResponse)
async def delete_inventory(
    inventory_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[InventoryService, Depends(_inventory_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> MessageResponse:
    workspace_id = _require_workspace(x_workspace_id)
    await svc.delete_inventory(principal, workspace_id, inventory_id)
    return MessageResponse(message="Inventory deleted")


@router.post("/reservations", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_reservation(
    body: ReservationCreate,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ReservationService, Depends(_reservation_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> dict:
    workspace_id = _require_workspace(x_workspace_id)
    reservation = await svc.reserve_stock(principal, workspace_id, **body.model_dump())
    return {"id": str(reservation.id), "status": reservation.status}


@router.post("/reservations/{reservation_id}/release", response_model=dict)
async def release_reservation(
    reservation_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ReservationService, Depends(_reservation_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> dict:
    workspace_id = _require_workspace(x_workspace_id)
    reservation = await svc.release_reservation(principal, workspace_id, reservation_id)
    return {"id": str(reservation.id), "status": reservation.status}


@router.post("/warehouses", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED)
async def create_warehouse(
    body: WarehouseCreate,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[WarehouseService, Depends(_warehouse_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> WarehouseResponse:
    workspace_id = _require_workspace(x_workspace_id)
    warehouse = await svc.create_warehouse(principal, workspace_id, **body.model_dump())
    return WarehouseResponse.model_validate(warehouse)


@router.get("/warehouses", response_model=list[WarehouseResponse])
async def list_warehouses(
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[WarehouseService, Depends(_warehouse_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> list[WarehouseResponse]:
    workspace_id = _require_workspace(x_workspace_id)
    rows = await svc.list_warehouses(principal, workspace_id)
    return [WarehouseResponse.model_validate(row) for row in rows]


@router.post("/transfers", response_model=dict, status_code=status.HTTP_201_CREATED)
async def transfer_inventory(
    body: TransferRequest,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[StockTransferService, Depends(_transfer_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> dict:
    workspace_id = _require_workspace(x_workspace_id)
    movement = await svc.transfer_inventory(principal, workspace_id, **body.model_dump())
    return {"id": str(movement.id), "status": "created"}


@router.post("/adjustments", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_adjustment(
    body: AdjustmentRequest,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[AdjustmentService, Depends(_adjustment_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> dict:
    workspace_id = _require_workspace(x_workspace_id)
    adjustment = await svc.manual_adjustment(principal, workspace_id, **body.model_dump())
    return {"id": str(adjustment.id), "status": "created"}
