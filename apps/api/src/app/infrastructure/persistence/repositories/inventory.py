"""Inventory repositories for internal enterprise inventory management."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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


class InventoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, inventory: InventoryModel) -> InventoryModel:
        self.session.add(inventory)
        await self.session.flush()
        return inventory

    async def get(self, workspace_id: uuid.UUID, inventory_id: uuid.UUID) -> InventoryModel | None:
        stmt = select(InventoryModel).where(
            InventoryModel.id == inventory_id,
            InventoryModel.workspace_id == workspace_id,
            InventoryModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_sku(self, workspace_id: uuid.UUID, sku: str) -> InventoryModel | None:
        stmt = select(InventoryModel).where(
            InventoryModel.workspace_id == workspace_id,
            InventoryModel.sku == sku,
            InventoryModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, workspace_id: uuid.UUID, *, offset: int = 0, limit: int = 50) -> Sequence[InventoryModel]:
        stmt = (
            select(InventoryModel)
            .where(
                InventoryModel.workspace_id == workspace_id,
                InventoryModel.deleted_at.is_(None),
            )
            .order_by(InventoryModel.updated_at.desc())
            .offset(max(0, offset))
            .limit(max(1, min(limit, 200)))
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self, workspace_id: uuid.UUID) -> int:
        stmt = select(InventoryModel).where(
            InventoryModel.workspace_id == workspace_id,
            InventoryModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return len(result.scalars().all())


class WarehouseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, warehouse: WarehouseModel) -> WarehouseModel:
        self.session.add(warehouse)
        await self.session.flush()
        return warehouse

    async def get(self, workspace_id: uuid.UUID, warehouse_id: uuid.UUID) -> WarehouseModel | None:
        stmt = select(WarehouseModel).where(
            WarehouseModel.id == warehouse_id,
            WarehouseModel.workspace_id == workspace_id,
            WarehouseModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, workspace_id: uuid.UUID, code: str) -> WarehouseModel | None:
        stmt = select(WarehouseModel).where(
            WarehouseModel.workspace_id == workspace_id,
            WarehouseModel.code == code,
            WarehouseModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, workspace_id: uuid.UUID) -> Sequence[WarehouseModel]:
        stmt = select(WarehouseModel).where(
            WarehouseModel.workspace_id == workspace_id,
            WarehouseModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class ReservationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, reservation: InventoryReservationModel) -> InventoryReservationModel:
        self.session.add(reservation)
        await self.session.flush()
        return reservation

    async def get(self, workspace_id: uuid.UUID, reservation_id: uuid.UUID) -> InventoryReservationModel | None:
        stmt = select(InventoryReservationModel).where(
            InventoryReservationModel.id == reservation_id,
            InventoryReservationModel.workspace_id == workspace_id,
            InventoryReservationModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class MovementRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, movement: InventoryMovementModel) -> InventoryMovementModel:
        self.session.add(movement)
        await self.session.flush()
        return movement


class AdjustmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, adjustment: InventoryAdjustmentModel) -> InventoryAdjustmentModel:
        self.session.add(adjustment)
        await self.session.flush()
        return adjustment


class InventoryLevelRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, level: InventoryLevelModel) -> InventoryLevelModel:
        self.session.add(level)
        await self.session.flush()
        return level


class InventorySnapshotRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, snapshot: InventorySnapshotModel) -> InventorySnapshotModel:
        self.session.add(snapshot)
        await self.session.flush()
        return snapshot


class WarehouseLocationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, location: WarehouseLocationModel) -> WarehouseLocationModel:
        self.session.add(location)
        await self.session.flush()
        return location
