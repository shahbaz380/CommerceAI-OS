# Plugin Foundation

**Version:** 1.0  

---

## Goal

Allow installing future modules **without changing core platform code paths**, only registering plugins that conform to a stable contract.

---

## Plugin Types

| Category | Examples | Repo path |
|----------|----------|-----------|
| Marketplace | Amazon, Shopify, Walmart, WooCommerce, TikTok Shop, Facebook Marketplace | `plugins/marketplace/`, `services/integration-*` |
| Accounting | QuickBooks-class, Xero-class (future) | `plugins/accounting/` |
| Email marketing | ESP providers | `plugins/email-marketing/` |
| CRM | HubSpot-class, etc. | `plugins/crm/` |
| Finance | Expense/tools | `plugins/finance/` |
| Inventory ERP | External ERP bridges | `plugins/inventory-erp/` |

Core marketplace adapters may live under `services/integration-*` while **packaging/enablement** is managed as plugins via `plugins/registry`.

---

## Plugin Contract (Logical)

Each plugin declares a **manifest** (future file, e.g. `plugin.manifest.json`):

| Field | Description |
|-------|-------------|
| `id` | `plugin.<domain>.<name>` |
| `version` | SemVer |
| `displayName` | Human name |
| `capabilities[]` | e.g. `sync.orders`, `publish.listings` |
| `permissions[]` | Required permission codes |
| `configSchema` | JSON schema for settings |
| `riskTier` | Side-effect risk classification |
| `entrypoint` | Module path |
| `minCoreVersion` | Compatibility |
| `featureFlag` | Optional enable flag |

---

## Runtime Rules

1. Core discovers plugins via **registry** only.  
2. Plugins receive **scoped** context (workspace, credentials handle, logger).  
3. Plugins **cannot** bypass tenancy or approval gates.  
4. Plugins disabled by default; enable per plan/tenant.  
5. Failures isolate to plugin circuit breakers.  

---

## Development Guidelines

- No direct imports of plugin internals from `apps/api` domain modules.  
- Shared types in `packages/*`.  
- Each plugin ships unit tests + contract tests.  
- Documentation under `docs/developer/plugins/` (later).  

---

## Future Expansion

- Hot load remote plugins (enterprise)  
- Plugin signing and verification  
- Marketplace of first-party plugins  
- Version negotiation and staged rollouts  

---

**End of Plugin Foundation**
