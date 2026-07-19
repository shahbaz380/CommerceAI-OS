# Prompt 19 – Enterprise eBay Inventory & Inventory Item Management Foundation

**Project:** CommerceAI OS – AI-Powered eCommerce & SEO Automation Platform  
**Type:** Implementation prompt (production-ready code)  
**Depends on:** Prompts 11–18 (complete)

---

## Completed implementation (do not redo)

| Prompt | Scope |
|--------|--------|
| 11 | Enterprise project initialization |
| 12 | Backend foundation |
| 13 | Database / persistence foundation |
| 14 | IAM |
| 15 | Org / workspace multi-tenant |
| 16 | Marketplace integration framework + eBay API foundation |
| 17 | Product catalog & listing management foundation |
| 18 | eBay OAuth account connection & authorization |

---

## IMPORTANT

Generate **REAL production-ready code**.

Inspect the existing repository before modifying files.

Do **NOT** redesign previous architecture.

**Reuse** existing:

- Configuration, DI, sessions, base models, repositories  
- AuthN/AuthZ, org/workspace tenancy  
- Marketplace framework, eBay adapter, OAuth tokens (Prompt 16–18)  
- Product catalog / variants / SKUs (Prompt 17)  
- Listing foundation (Prompt 17) — inventory may **link** to products/variants/listings but must not reimplement catalog  
- Logging, exceptions, API standards, testing conventions  
- Encrypted token access via connection services (never expose tokens in APIs)

Do **NOT** duplicate OAuth, connection, or product catalog code. Extend only.

---

## PRIMARY GOAL

Build an **enterprise inventory foundation** that:

1. Maintains **internal inventory truth** per workspace (quantity, SKU, location placeholders).  
2. Maps internal inventory to **eBay Inventory API concepts** (inventory item, SKU, offer linkage placeholders).  
3. Uses **connected eBay accounts** from Prompt 18 for authenticated gateway calls.  
4. Supports **sandbox and production**.  
5. Remains **marketplace-pluggable** (eBay first; Amazon/Shopify later).

After this prompt, the platform should be able to:

- Create / update / get / delete **internal inventory items**  
- Link inventory items to **products / variants**  
- Upsert **eBay inventory items** (Sell Inventory API) via gateway  
- Bulk create/update inventory items (foundation)  
- Read eBay inventory item by SKU  
- Delete eBay inventory item by SKU  
- Track **sync status** and errors per item / connection  
- Refresh tokens automatically before eBay calls (`ensure_fresh_access_token`)  
- Enforce tenant isolation and RBAC  

---

## OUT OF SCOPE (explicit)

Do **NOT** implement:

- Live **listing publish** / offer publish (beyond inventory item identity)  
- Full **Offer** create/publish workflow (may add Offer **placeholder** entity only if required for FK; no business publish)  
- Orders / fulfillment / shipping  
- Buyer messages / returns  
- Dynamic pricing / AI agents  
- Warehouse WMS / multi-warehouse deep ops (single default location + extensible location model is OK)  
- Stock movements ledger / accounting COGS  
- Analytics dashboards  

If Offer entities are needed as stubs for future Prompt 20, keep them minimal and unpublished.

---

## Technology stack

Python 3.12 · FastAPI · SQLAlchemy 2.x · Pydantic v2 · PostgreSQL · Redis · Alembic · HTTPX · Pytest · Docker

---

## Architecture requirements

Use:

- Clean Architecture + DDD + SOLID  
- Repository + Service layers  
- Adapter / Gateway / Factory (reuse marketplace patterns)  
- Async programming  
- Domain events  
- Specification / filters for search  
- Unit of Work / session transactions consistent with existing code  
- Enterprise coding standards already in repo  

### Domain boundaries

**1. Internal Inventory Domain (marketplace-independent)**  
Owns: inventory items, quantities, SKU binding, locations (simple), reservations placeholder, sync intent state.

**2. eBay Inventory Integration Domain**  
Owns: mapping to eBay inventory item SKU, payload builders, gateway calls, sync results, provider errors.

Internal catalog (Prompt 17) remains source of product identity; inventory references `product_id` / `variant_id` / `sku`.

---

## eBay Inventory API foundation (real HTTP, authenticated)

Implement gateway methods against eBay Sell **Inventory API** (sandbox + production base URLs already patterned in `EbayApiGateway`):

Suggested operations (adjust paths to current eBay Sell Inventory API):

| Operation | Typical path (verify against eBay docs when coding) |
|-----------|------------------------------------------------------|
| Create/replace inventory item | `PUT /sell/inventory/v1/inventory_item/{sku}` |
| Get inventory item | `GET /sell/inventory/v1/inventory_item/{sku}` |
| Delete inventory item | `DELETE /sell/inventory/v1/inventory_item/{sku}` |
| Bulk create/update | `POST /sell/inventory/v1/bulk_create_or_replace_inventory_item` |
| Get inventory items | `GET /sell/inventory/v1/inventory_item` (limit/offset) |

Requirements:

- Use **Bearer access token** from encrypted storage via connection  
- Call `ensure_fresh_access_token` (or equivalent) before requests  
- Translate HTTP errors via existing marketplace error mapping  
- Log API calls to `marketplace_api_logs` (no token logging)  
- Support idempotent upsert by SKU  
- Parse eBay error payload structure into platform errors  

**Mock all eBay HTTP in tests** — never call live eBay in CI.

---

## Internal inventory model

### Inventory item

Support fields such as:

- id, organization_id, workspace_id  
- product_id (optional FK to products)  
- product_variant_id (optional FK)  
- sku (required, tenant-unique)  
- title / display_name  
- condition  
- quantity_available  
- quantity_reserved (placeholder, default 0)  
- quantity_on_hand (computed or stored consistently)  
- location_key / merchant_location_key placeholder  
- status: `draft` \| `active` \| `inactive` \| `archived`  
- metadata JSON  
- audit + version + soft delete  
- last_synced_at, last_sync_status, last_sync_error  

### Inventory ↔ marketplace mapping

- inventory_item_id  
- marketplace_connection_id  
- channel (`ebay`)  
- external_sku (usually same as internal SKU)  
- external_inventory_item_key / eBay SKU  
- sync_status: `never` \| `pending` \| `synced` \| `error` \| `deleted_remote`  
- last_remote_hash / payload fingerprint optional  
- last_synced_at, last_error  
- metadata  

### Optional location foundation

Simple `inventory_locations` (workspace-scoped):

- key, name, address placeholders, status  
- default location flag  

No carrier/WMS logic.

### Sync history

Reuse/extend `marketplace_sync_history` with `entity_type=inventory_item` or dedicated `inventory_sync_jobs` if cleaner — prefer extending existing sync history if it fits.

---

## Domain rules

1. SKU unique per workspace (align with catalog SKU rules where linked).  
2. If linked to variant, SKU should match variant SKU unless explicitly overridden (document rule).  
3. Quantity cannot be negative.  
4. Cannot sync to eBay without `connected` marketplace connection in same workspace.  
5. Cross-tenant access forbidden.  
6. Soft-delete local item does not auto-delete remote unless explicit “delete remote” use case.  
7. Optimistic concurrency on inventory item updates.  

---

## Application services (use cases)

Implement services such as:

**Internal**

- CreateInventoryItem  
- UpdateInventoryItem  
- GetInventoryItem  
- SearchInventoryItems  
- ArchiveInventoryItem  
- AdjustQuantity (simple set/delta; not full ledger)  
- LinkToProduct / LinkToVariant  

**eBay sync**

- PushInventoryItemToEbay (create/replace)  
- PullInventoryItemFromEbay (get by SKU)  
- DeleteInventoryItemOnEbay  
- BulkPushInventoryItems  
- SyncInventoryItemStatus / ValidateRemoteInventoryItem  

**Connection-aware**

- ResolveDefaultEbayConnectionForWorkspace  
- EnsureFreshTokenForConnection  

Emit domain events, e.g.:

- `inventory.item.created`  
- `inventory.item.updated`  
- `inventory.item.archived`  
- `inventory.quantity.adjusted`  
- `inventory.ebay.push.succeeded` / `failed`  
- `inventory.ebay.deleted`  

---

## Permissions (extend IAM seed)

Add and grant appropriately (owner/manager/staff/read_only):

- `inventory.read`  
- `inventory.write`  
- `inventory.adjust`  
- `inventory.sync`  
- `inventory.delete`  

Reuse existing `inventory.read` / `inventory.write` if already present; add granular codes if needed without breaking seed idempotency.

---

## API endpoints (versioned)

All require auth + workspace scope (`X-Workspace-Id` and/or path param consistent with existing marketplace routes).

### Internal inventory

```text
POST   /api/v1/inventory/items
GET    /api/v1/inventory/items
GET    /api/v1/inventory/items/{item_id}
PATCH  /api/v1/inventory/items/{item_id}
DELETE /api/v1/inventory/items/{item_id}
POST   /api/v1/inventory/items/{item_id}/adjust
GET    /api/v1/inventory/items/by-sku/{sku}
```

### eBay inventory integration

```text
POST   /api/v1/marketplaces/ebay/workspaces/{workspace_id}/inventory/push
POST   /api/v1/marketplaces/ebay/workspaces/{workspace_id}/inventory/push/{item_id}
GET    /api/v1/marketplaces/ebay/workspaces/{workspace_id}/inventory/remote/{sku}
DELETE /api/v1/marketplaces/ebay/workspaces/{workspace_id}/inventory/remote/{sku}
POST   /api/v1/marketplaces/ebay/workspaces/{workspace_id}/inventory/bulk-push
GET    /api/v1/marketplaces/ebay/workspaces/{workspace_id}/inventory/mappings
POST   /api/v1/marketplaces/ebay/workspaces/{workspace_id}/inventory/{item_id}/sync
```

(Adjust paths slightly if needed to match router style; keep `/api/v1` versioning.)

Query params: `connection_id` optional (default connection from Prompt 18).

---

## Pydantic schemas

Create request/response models for all endpoints, including:

- InventoryItemCreate / Update / Response / ListResponse  
- InventoryAdjustRequest  
- InventorySearchFilters  
- EbayInventoryPushRequest / Response  
- EbayRemoteInventoryItemResponse  
- InventoryMappingResponse  
- BulkPushRequest / BulkPushResult  

Never include access/refresh tokens in responses.

---

## Database / Alembic

Create migration only for **new** inventory tables/columns, e.g.:

`20260718_0007_inventory_foundation` (verify chain after `0006`)

Suggested tables:

- `inventory_items`  
- `inventory_item_marketplace_mappings`  
- `inventory_locations` (optional simple)  
- extend sync/history if needed  

Do **not** recreate marketplace_connections or products tables.

Include upgrade + downgrade, indexes, FKs, uniques `(workspace_id, sku)`.

---

## Gateway / adapter extensions

Extend **existing** eBay packages:

- `EbayApiGateway`: inventory_item CRUD/bulk methods  
- Optional `EbayInventoryAdapter` or methods on a dedicated inventory gateway used by application service  
- Reuse `AsyncHttpClient` retry/rate-limit behavior  
- Payload builder: map internal inventory → eBay inventory item JSON (product aspects minimal from catalog if linked)

Do not implement offer publish.

---

## Caching

Optional Redis:

- Cache remote get-by-SKU short TTL  
- Cache default connection id per workspace  

Tenant-safe keys; invalidate on push/delete/disconnect.

---

## Security

- Workspace membership required  
- Permission checks on write/sync/delete  
- Encrypt nothing new if tokens already encrypted  
- Mask secrets in logs  
- Audit inventory mutations and sync outcomes  
- Validate SKU/quantity inputs  

---

## Testing

Must include:

**Unit**

- Quantity rules, SKU validation, status transitions  
- Payload builder mapping  
- Error translation  

**Integration / API**

- CRUD inventory item tenant isolation  
- Duplicate SKU conflict  
- Push success with **mocked** eBay HTTP  
- Push failure when connection not connected  
- Token refresh invoked when access expired (mock)  
- Bulk push partial success handling  
- Delete remote mocked  
- Permission denied cases  

**Migration**

- Models register on metadata; upgrade path consistent  

Use `httpx.MockTransport` or AsyncMock on gateway — **no live eBay**.

Target: all existing tests still pass + new suite green.

---

## Documentation

Create/update under `apps/api/docs/`:

1. Inventory Architecture Guide  
2. eBay Inventory Integration Guide  
3. Inventory API Guide  
4. Sync lifecycle / error handling  
5. Update main `apps/api/README.md`  
6. Update prompt history if present (`docs/prompts/`)

Include diagrams:

- Internal inventory vs eBay inventory item  
- Push/sync sequence (token ensure → PUT → mapping update)  
- Multi-account connection selection  

---

## Implementation layers checklist

Complete all of:

- [ ] Domain (enums, exceptions, events, rules)  
- [ ] ORM models + repositories  
- [ ] Alembic migration  
- [ ] eBay gateway inventory methods  
- [ ] Application services  
- [ ] API routes + schemas  
- [ ] Permissions seed updates  
- [ ] Tests  
- [ ] Documentation  

Do not stop at models only.

---

## Output requirements (end of implementation)

Provide:

1. Existing repository analysis  
2. Updated repository tree  
3. Files created / modified  
4. Architecture explanation  
5. Sequence diagrams (connect token → push inventory)  
6. ER explanation  
7. API summary  
8. Permission matrix  
9. Security decisions  
10. Scalability notes  
11. Migration summary  
12. Test summary + commands  
13. Implementation summary  

Explicitly confirm out-of-scope items were not built.

---

## Final statements (required)

End with:

**Prompt 19 – Enterprise eBay Inventory & Inventory Item Management Foundation is complete.**

Then ask:

**Ready to continue with Prompt 20 – Enterprise eBay Offer Management & Listing Publication Foundation?**

---

## Suggested Prompt 20 (preview only — do not implement now)

Offer create/update, publish/unpublish listing, price/quantity on offer, listing↔offer binding, publish validation — building on catalog listings + inventory items + OAuth.
