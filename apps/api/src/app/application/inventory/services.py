"""Inventory application services."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.identity.authorization import Principal
from app.application.tenancy.tenant_access import TenantAccessService
from app.domain.inventory.enums import AdjustmentReason, InventoryStatus, MovementType, ReservationStatus, WarehouseType
from app.domain.inventory.exceptions import InventoryNotFoundError, InventoryValidationError
from app.domain.inventory.value_objects import Quantity, SKU
from app.infrastructure.persistence.models.inventory import (
    InventoryAdjustmentModel,
    InventoryLevelModel,
    InventoryModel,
    InventoryMovementModel,
    InventoryReservationModel,
    InventorySnapshotModel,
    WarehouseLocationModel,
    WarehouseModel,
)
from app.infrastructure.persistence.repositories.inventory import (
    AdjustmentRepository,
    InventoryRepository,
    MovementRepository,
    ReservationRepository,
    WarehouseRepository,
)
from app.shared.exceptions import ValidationAppError


class InventoryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.inventories = InventoryRepository(session)
        self.access = TenantAccessService(session)
        self.movements = MovementRepository(session)

    async def create_inventory(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        *,
        sku: str,
        warehouse_id: uuid.UUID | None = None,
        quantity: int = 0,
        product_id: uuid.UUID | None = None,
    ) -> InventoryModel:
        await self.access.require_workspace_member(principal, workspace_id)
        sku_value = SKU(sku).value
        if await self.inventories.get_by_sku(workspace_id, sku_value):
            raise InventoryValidationError("Inventory SKU already exists", details=[{"field": "sku", "issue": "duplicate"}])
        model = InventoryModel(
            tenant_id=workspace_id,
            workspace_id=workspace_id,
            organization_id=uuid.uuid4(),
            sku=sku_value,
            warehouse_id=warehouse_id,
            product_id=product_id,
            status=InventoryStatus.ACTIVE,
            available_quantity=max(0, int(quantity)),
            reserved_quantity=0,
            physical_quantity=max(0, int(quantity)),
            last_known_cost=Decimal("0.00"),
            created_by=principal.user_id,
            updated_by=principal.user_id,
        )
        await self.inventories.add(model)
        await self.session.flush()
        level = InventoryLevelModel(
            tenant_id=workspace_id,
            workspace_id=workspace_id,
            organization_id=model.organization_id,
            inventory_id=model.id,
            warehouse_id=warehouse_id,
            sku=sku_value,
            status=InventoryStatus.ACTIVE,
            available_quantity=model.available_quantity,
            reserved_quantity=model.reserved_quantity,
            physical_quantity=model.physical_quantity,
            low_stock_threshold=0,
            out_of_stock_threshold=0,
        )
        self.session.add(level)
        await self.session.flush()
        return model

    async def update_inventory(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        inventory_id: uuid.UUID,
        **fields: object,
    ) -> InventoryModel:
        await self.access.require_workspace_member(principal, workspace_id)
        inventory = await self.inventories.get(workspace_id, inventory_id)
        if inventory is None:
            raise InventoryNotFoundError()
        for key in ("status", "warehouse_id", "product_id", "sku", "reorder_point", "reorder_quantity"):
            if key in fields and fields[key] is not None:
                setattr(inventory, key, fields[key])
        inventory.updated_by = principal.user_id
        inventory.touch()
        await self.session.flush()
        return inventory

    async def get_inventory(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        inventory_id: uuid.UUID,
    ) -> InventoryModel:
        await self.access.require_workspace_member(principal, workspace_id, min_role="read_only")
        inventory = await self.inventories.get(workspace_id, inventory_id)
        if inventory is None:
            raise InventoryNotFoundError()
        return inventory

    async def delete_inventory(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        inventory_id: uuid.UUID,
    ) -> None:
        await self.access.require_workspace_member(principal, workspace_id)
        inventory = await self.inventories.get(workspace_id, inventory_id)
        if inventory is None:
            raise InventoryNotFoundError()
        await self.inventories.delete(inventory)


class ReservationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repositories = ReservationRepository(session)
        self.inventory_repo = InventoryRepository(session)
        self.access = TenantAccessService(session)

    async def reserve_stock(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        *,
        inventory_id: uuid.UUID,
        quantity: int,
        reservation_id: uuid.UUID | None = None,
    ) -> InventoryReservationModel:
        await self.access.require_workspace_member(principal, workspace_id)
        quantity_value = Quantity(quantity).value
        inventory = await self.inventory_repo.get(workspace_id, inventory_id)
        if inventory is None:
            raise InventoryNotFoundError()
        if inventory.available_quantity < quantity_value:
            raise InventoryValidationError("Insufficient available stock", details=[{"field": "quantity", "issue": "insufficient"}])
        reservation = InventoryReservationModel(
            tenant_id=workspace_id,
            workspace_id=workspace_id,
            organization_id=inventory.organization_id,
            inventory_id=inventory.id,
            warehouse_id=inventory.warehouse_id,
            reservation_id=reservation_id or uuid.uuid4(),
            quantity=quantity_value,
            status=ReservationStatus.ACTIVE,
            created_by=principal.user_id,
            updated_by=principal.user_id,
        )
        inventory.available_quantity -= quantity_value
        inventory.reserved_quantity += quantity_value
        await self.repositories.add(reservation)
        await self.session.flush()
        return reservation

    async def release_reservation(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        reservation_id: uuid.UUID,
    ) -> InventoryReservationModel:
        await self.access.require_workspace_member(principal, workspace_id)
        reservation = await self.repositories.get(workspace_id, reservation_id)
        if reservation is None:
            raise InventoryValidationError("Reservation not found", details=[{"field": "reservation_id", "issue": "not_found"}])
        if reservation.status != ReservationStatus.ACTIVE:
            raise InventoryValidationError("Reservation is not active", details=[{"field": "reservation_id", "issue": "inactive"}])
        inventory = await self.inventory_repo.get(workspace_id, reservation.inventory_id)
        if inventory is not None:
            inventory.available_quantity += reservation.quantity
            inventory.reserved_quantity -= reservation.quantity
        reservation.status = ReservationStatus.RELEASED
        reservation.updated_by = principal.user_id
        await self.session.flush()
        return reservation

    async def cancel_reservation(self, principal: Principal, workspace_id: uuid.UUID, reservation_id: uuid.UUID) -> InventoryReservationModel:
        return await self.release_reservation(principal, workspace_id, reservation_id)

    async def expire_reservation(self, principal: Principal, workspace_id: uuid.UUID, reservation_id: uuid.UUID) -> InventoryReservationModel:
        await self.access.require_workspace_member(principal, workspace_id)
        reservation = await self.repositories.get(workspace_id, reservation_id)
        if reservation is None:
            raise InventoryValidationError("Reservation not found", details=[{"field": "reservation_id", "issue": "not_found"}])
        reservation.status = ReservationStatus.EXPIRED
        reservation.updated_by = principal.user_id
        await self.session.flush()
        return reservation


class WarehouseService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repositories = WarehouseRepository(session)
        self.access = TenantAccessService(session)

    async def create_warehouse(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        *,
        code: str,
        name: str,
        warehouse_type: str = WarehouseType.WAREHOUSE,
    ) -> WarehouseModel:
        await self.access.require_workspace_member(principal, workspace_id)
        if await self.repositories.get_by_code(workspace_id, code):
            raise InventoryValidationError("Warehouse code already exists", details=[{"field": "code", "issue": "duplicate"}])
        warehouse = WarehouseModel(
            tenant_id=workspace_id,
            workspace_id=workspace_id,
            organization_id=uuid.uuid4(),
            code=code.upper(),
            name=name,
            warehouse_type=warehouse_type,
            status="active",
            created_by=principal.user_id,
            updated_by=principal.user_id,
        )
        await self.repositories.add(warehouse)
        await self.session.flush()
        return warehouse

    async def update_warehouse(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        warehouse_id: uuid.UUID,
        **fields: object,
    ) -> WarehouseModel:
        await self.access.require_workspace_member(principal, workspace_id)
        warehouse = await self.repositories.get(workspace_id, warehouse_id)
        if warehouse is None:
            raise InventoryValidationError("Warehouse not found", details=[{"field": "warehouse_id", "issue": "not_found"}])
        for key in ("name", "warehouse_type", "status", "address_line1", "city", "country"):
            if key in fields and fields[key] is not None:
                setattr(warehouse, key, fields[key])
        warehouse.updated_by = principal.user_id
        await self.session.flush()
        return warehouse

    async def list_warehouses(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
    ) -> Sequence[WarehouseModel]:
        await self.access.require_workspace_member(principal, workspace_id, min_role="read_only")
        return await self.repositories.list(workspace_id)


class StockTransferService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.warehouses = WarehouseRepository(session)
        self.inventory_repo = InventoryRepository(session)
        self.movements = MovementRepository(session)

    async def transfer_inventory(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        *,
        inventory_id: uuid.UUID,
        source_warehouse_id: uuid.UUID,
        destination_warehouse_id: uuid.UUID,
        quantity: int,
    ) -> InventoryMovementModel:
        inventory = await self.inventory_repo.get(workspace_id, inventory_id)
        if inventory is None:
            raise InventoryNotFoundError()
        source = await self.warehouses.get(workspace_id, source_warehouse_id)
        destination = await self.warehouses.get(workspace_id, destination_warehouse_id)
        if source is None or destination is None:
            raise InventoryValidationError("Warehouse not found", details=[{"field": "warehouse", "issue": "not_found"}])
        if inventory.available_quantity < quantity:
            raise InventoryValidationError("Insufficient available stock for transfer", details=[{"field": "quantity", "issue": "insufficient"}])
        inventory.available_quantity -= quantity
        destination_available = (destination.capacity or 0) - (destination.current_utilization or 0)
        if destination_available < quantity:
            raise InventoryValidationError("Destination warehouse capacity exceeded", details=[{"field": "warehouse_id", "issue": "capacity"}])
        movement = InventoryMovementModel(
            tenant_id=workspace_id,
            workspace_id=workspace_id,
            organization_id=inventory.organization_id,
            inventory_id=inventory.id,
            source_warehouse_id=source_warehouse_id,
            destination_warehouse_id=destination_warehouse_id,
            movement_type=MovementType.TRANSFER,
            quantity=quantity,
            reason="transfer",
            created_by=principal.user_id,
            updated_by=principal.user_id,
        )
        await self.movements.add(movement)
        await self.session.flush()
        return movement


class AdjustmentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.inventory_repo = InventoryRepository(session)
        self.adjustments = AdjustmentRepository(session)
        self.movements = MovementRepository(session)

    async def increase_stock(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        inventory_id: uuid.UUID,
        quantity: int,
    ) -> InventoryAdjustmentModel:
        return await self.manual_adjustment(principal, workspace_id, inventory_id, quantity, reason=AdjustmentReason.CYCLE_COUNT)

    async def decrease_stock(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        inventory_id: uuid.UUID,
        quantity: int,
    ) -> InventoryAdjustmentModel:
        return await self.manual_adjustment(principal, workspace_id, inventory_id, -abs(quantity), reason=AdjustmentReason.CYCLE_COUNT)

    async def manual_adjustment(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        inventory_id: uuid.UUID,
        quantity: int,
        *,
        reason: str = AdjustmentReason.MANUAL,
    ) -> InventoryAdjustmentModel:
        if quantity == 0:
            raise InventoryValidationError("Adjustment quantity cannot be zero", details=[{"field": "quantity", "issue": "zero"}])
        inventory = await self.inventory_repo.get(workspace_id, inventory_id)
        if inventory is None:
            raise InventoryNotFoundError()
        delta = int(quantity)
        inventory.available_quantity += delta
        inventory.physical_quantity += delta
        adjustment = InventoryAdjustmentModel(
            tenant_id=workspace_id,
            workspace_id=workspace_id,
            organization_id=inventory.organization_id,
            inventory_id=inventory.id,
            warehouse_id=inventory.warehouse_id,
            quantity=abs(delta),
            adjustment_type="manual" if delta > 0 else "decrement",
            reason=reason,
            created_by=principal.user_id,
            updated_by=principal.user_id,
        )
        await self.adjustments.add(adjustment)
        await self.session.flush()
        return adjustment

    async def cycle_count_adjustment(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        inventory_id: uuid.UUID,
        quantity: int,
    ) -> InventoryAdjustmentModel:
        return await self.manual_adjustment(principal, workspace_id, inventory_id, quantity, reason=AdjustmentReason.CYCLE_COUNT)


class InventoryQueryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = InventoryRepository(session)

    async def list_inventory(self, workspace_id: uuid.UUID, *, offset: int = 0, limit: int = 50) -> tuple[Sequence[InventoryModel], int]:
        items = await self.repo.list(workspace_id=workspace_id, offset=offset, limit=limit)
        total = await self.repo.count(workspace_id=workspace_id)
        return items, total
