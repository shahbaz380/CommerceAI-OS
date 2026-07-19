# Inventory Management Foundation

This directory documents the internal warehouse inventory foundation added to CommerceAI OS.

## Scope

- Internal inventory records only
- Tenant-scoped warehouse and reservation workflows
- No marketplace inventory synchronization
- No eBay sync integration

## Core entities

- Inventory records
- Warehouses
- Warehouse locations
- Inventory levels
- Reservations
- Stock movements
- Adjustments
- Snapshots

## API surface

- `GET /api/v1/inventory`
- `POST /api/v1/inventory`
- `GET /api/v1/inventory/{id}`
- `PATCH /api/v1/inventory/{id}`
- `DELETE /api/v1/inventory/{id}`
- `POST /api/v1/reservations`
- `POST /api/v1/reservations/{id}/release`
- `POST /api/v1/warehouses`
- `GET /api/v1/warehouses`
- `POST /api/v1/transfers`
- `POST /api/v1/adjustments`
