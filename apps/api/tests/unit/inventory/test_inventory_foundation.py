from __future__ import annotations

import uuid

import pytest

from app.application.identity.authorization import Principal
from app.application.inventory.services import InventoryService, ReservationService, WarehouseService
from app.domain.inventory.enums import ReservationStatus
from app.infrastructure.persistence.models.identity import UserModel
from app.infrastructure.persistence.models.inventory import InventoryModel, WarehouseModel
from app.infrastructure.persistence.models.tenancy import OrganizationModel, WorkspaceModel


@pytest.mark.asyncio
async def test_inventory_reservation_flow(db_session):
    principal = Principal(
        user_id=uuid.uuid4(),
        email="admin@example.com",
        roles=["manager"],
        permissions=[],
        is_superuser=False,
    )
    workspace_id = uuid.uuid4()
    org_id = uuid.uuid4()

    db_session.add(
        UserModel(
            id=principal.user_id,
            email=principal.email,
            username="inventory-admin",
            password_hash="test-hash",
            is_active=True,
        )
    )
    db_session.add(
        OrganizationModel(
            id=org_id,
            name="Inventory Org",
            slug="inventory-org",
            owner_user_id=principal.user_id,
        )
    )
    db_session.add(
        WorkspaceModel(
            id=workspace_id,
            organization_id=org_id,
            name="Inventory Workspace",
            slug="inventory-workspace",
            status="active",
            is_default=True,
        )
    )
    await db_session.flush()

    inventory_svc = InventoryService(db_session)
    reservation_svc = ReservationService(db_session)
    warehouse_svc = WarehouseService(db_session)

    warehouse = await warehouse_svc.create_warehouse(
        principal,
        workspace_id,
        code="NDC",
        name="North DC",
    )

    inventory = await inventory_svc.create_inventory(
        principal,
        workspace_id,
        sku="SKU-1001",
        warehouse_id=warehouse.id,
        quantity=10,
    )

    reservation = await reservation_svc.reserve_stock(
        principal,
        workspace_id,
        inventory_id=inventory.id,
        quantity=3,
    )

    assert reservation.status == ReservationStatus.ACTIVE
    assert inventory.available_quantity == 7
    assert inventory.reserved_quantity == 3

    released = await reservation_svc.release_reservation(principal, workspace_id, reservation.id)
    assert released.status == ReservationStatus.RELEASED
