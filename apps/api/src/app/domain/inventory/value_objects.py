"""Value objects for internal inventory management."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.shared.exceptions import ValidationAppError


@dataclass(frozen=True, slots=True)
class Quantity:
    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValidationAppError(
                "Quantity cannot be negative",
                details=[{"field": "quantity", "issue": "negative"}],
            )

    def __int__(self) -> int:
        return self.value


@dataclass(frozen=True, slots=True)
class SKU:
    value: str

    def __post_init__(self) -> None:
        text = (self.value or "").strip().upper()
        if len(text) < 3 or not text.replace("-", "").isalnum():
            raise ValidationAppError(
                "SKU format is invalid",
                details=[{"field": "sku", "issue": "format"}],
            )
        object.__setattr__(self, "value", text)


@dataclass(frozen=True, slots=True)
class WarehouseCode:
    value: str

    def __post_init__(self) -> None:
        if not self.value or len(self.value.strip()) < 2:
            raise ValidationAppError(
                "Warehouse code is invalid",
                details=[{"field": "warehouse_code", "issue": "format"}],
            )
        object.__setattr__(self, "value", self.value.strip().upper())


@dataclass(frozen=True, slots=True)
class LocationCode:
    value: str

    def __post_init__(self) -> None:
        if not self.value or len(self.value.strip()) < 1:
            raise ValidationAppError(
                "Location code is invalid",
                details=[{"field": "location_code", "issue": "format"}],
            )
        object.__setattr__(self, "value", self.value.strip().upper())


@dataclass(frozen=True, slots=True)
class ReservationId:
    value: UUID


@dataclass(frozen=True, slots=True)
class MovementId:
    value: UUID


@dataclass(frozen=True, slots=True)
class InventoryId:
    value: UUID
