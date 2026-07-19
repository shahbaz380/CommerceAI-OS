# Inventory API

## Inventory

### POST /api/v1/inventory
Creates an inventory row for a workspace-scoped SKU.

### GET /api/v1/inventory
Lists inventory rows for the tenant workspace.

### GET /api/v1/inventory/{id}
Fetches a single inventory row.

### PATCH /api/v1/inventory/{id}
Updates supported inventory fields.

### DELETE /api/v1/inventory/{id}
Deletes an inventory row.

## Reservations

### POST /api/v1/reservations
Creates a reservation against available inventory.

### POST /api/v1/reservations/{id}/release
Releases an active reservation back to available inventory.

## Warehouses

### POST /api/v1/warehouses
Creates an internal warehouse record.

### GET /api/v1/warehouses
Lists warehouses visible to the workspace.

## Transfers and Adjustments

### POST /api/v1/transfers
Creates a transfer movement between warehouses.

### POST /api/v1/adjustments
Creates a stock adjustment entry.
