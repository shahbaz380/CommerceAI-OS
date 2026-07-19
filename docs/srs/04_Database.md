# Software Requirements Specification (SRS) — Part 4
## CommerceAI OS – Enterprise Database Architecture & Data Model

**Document Version:** 1.0  
**Status:** Logical Data Architecture Baseline  
**Date:** 2026-07-16  
**Predecessors:** Parts 1–3  

---

### Document Control

| Field | Value |
|--------|--------|
| Document Part | Part 4 — Database Architecture & Data Model |
| Excluded | SQL DDL/DML, ORM code, physical index scripts |
| Next Part | Part 5 — API Architecture |

---

# SECTION 1 — Database Strategy

## Primary Technology
**PostgreSQL** (managed cloud service) as OLTP system of record.

## Complements (polyglot by maturity)
Redis (sessions, rate limits, hot cache) · Object storage (images/exports) · Optional search engine · Optional analytical warehouse · Queue/stream brokers (related, not DB)

## Why PostgreSQL
Relational integrity for commerce · Multi-tenant SaaS patterns · JSONB for channel payloads · MVCC · Ecosystem · RLS option · AI structured + flexible payloads

## Scalability
Vertical early · Connection pooling · Read replicas · Partition append-only tables · Archive cold data · Tenant keys for future sharding · CQRS-lite projections for dashboards

## HA / Backup / DR
Multi-AZ primary+standby · PITR/WAL · Encrypted snapshots · Restore drills · Optional cross-region copy · Rebuild order: tenants → IAM → channels → catalog → inventory → orders → AI/logs

## Partitioning Candidates
Sync logs · login/security logs · agent/execution/prompt history · notification history · price/stock history · audit/system logs · analytics snapshots

## Indexing & Performance
Tenant composite indexes · External natural keys · Partial indexes for active sets · Selective JSONB GIN · Keyset pagination · Idempotency keys · Jobs for bulk · Media in object storage not DB BLOBs

---

# SECTION 2 — Core Database Modules (Logical)

**Global conventions:** workspace/tenant scope · soft delete where recovery matters · timestamps + actors · money + currency · channel JSONB isolated from canonical required columns

## 1. User Management
`users`, `roles`, `permissions`, `role_permissions`, `user_roles`, `sessions`, `login_history`, `api_tokens`, security/reset/verification token tables  
**Security:** hash passwords/tokens; minimize PII in logs

## 2. Company & Workspace
`companies`, `business_profiles`, `workspaces`, `workspace_members`, `workspace_invitations`, settings  
**Primary isolation key:** `workspace_id`

## 3. eBay Integration
`connected_accounts`, `oauth_tokens` (encrypted), `sync_jobs`, `sync_logs`, `account_status_snapshots`, `connection_history`  
**Unique:** (workspace, channel_type, external_account_id)

## 4. Listings
`products`, `listings`, `categories`, `listing_images`, `listing_templates`, `listing_seo_metadata`, `listing_history`, identifiers  
**Multi-channel ready:** product 1—N listings

## 5. Inventory
`inventory_items`, `warehouses`, `inventory_levels`, `stock_history`, `supplier_inventory`, `low_stock_alerts`, `inventory_policies`

## 6. Suppliers
`suppliers`, contacts, `supplier_products`, `supplier_pricing`, ratings, performance snapshots

## 7. Pricing
`price_rules`, `profit_rules`, `competitor_prices`, `historical_prices`, `pricing_recommendations`, `price_change_requests`

## 8. Orders
`orders`, `order_items`, `payments`, `shipments`, `tracking_numbers`, `refunds`, `returns`, `order_status_history`  
**Rule:** prefer immutable financial history (no casual hard delete)

## 9. Customers
`customers`, `customer_addresses`, `communication_history`, `feedback_records`, `support_tickets`, ticket messages

## 10. Analytics
Report definitions, sales/profit/revenue snapshots, expenses, forecast runs/points, KPI definitions/values, export jobs  
**Rule:** snapshots immutable; recompute = new version; quality flags required

## 11. AI System
`ai_conversations`, `ai_messages`, `ai_tasks`, dependencies, `ai_recommendations`, `ai_decisions`, `agent_logs`, `prompt_history`, `ai_execution_logs`, `ai_memory_records`, `ai_approval_requests`  
**Rule:** gated execution requires policy-satisfying decision

## 12. Notifications
Preferences, templates, events, deliveries, history, channel endpoints

## 13. Blog & SEO
Sites/blogs, articles, keywords, article_keywords, seo_scores, content_calendar, internal_links, revisions

## 14. Guest Posting CRM
Clients, vendors, websites, campaigns, outreach emails, deals, invoices, activities, relationships  
**Rule:** sent outreach requires approval reference

## 15. Subscription System
Plans, entitlements, subscriptions, items, billing invoices/payments, usage_records, usage_limits, breach events  
**PCI:** provider tokens only; no raw card data

## 16. Admin System
`audit_logs`, system/error/security/monitoring logs (append-oriented, time-partitioned)

---

# SECTION 3 — Relationships

**1:1** Listing–SEO metadata; User–security settings  
**1:N** Workspace→accounts/products/orders/AI; Order→items/shipments  
**M:N** Roles–Permissions; Users–Workspaces; Articles–Keywords  

**Delete philosophy:** soft-delete operational masters · wipe tokens on revoke · retain financial/audit · partition-drop logs · stable surrogate IDs (no PK updates)

---

# SECTION 4 — Security

Encryption at rest/in transit · field-level for tokens/tax/phone · KMS · RBAC + tenant predicates + optional RLS · audit trails · GDPR export/erase/anonymization readiness · agency client isolation

---

# SECTION 5 — Performance

Tenant+time indexes · entitlement/session cache · keyset pagination · OLTP vs analytics separation · archive partitions · monitor connections, lag, bloat, backups

---

# SECTION 6 — Scale Path (No Logical Redesign)

| Users | Posture |
|-------|---------|
| 10–100 | Single primary + backups |
| 1,000 | Replica + partition logs |
| 10,000 | Multi-replica, archive, async analytics |
| 100,000 | OLTP/OLAP split, hot-tenant controls |
| 1,000,000 | Tenant sharding/cells; same logical schema |

---

# SECTION 7 — Multi-Channel Expansion

Canonical entities + `channel_type` + extension/payload tables. Adding Amazon/Shopify/Walmart/Woo/TikTok/Facebook = adapters and additive tables, not core rewrites.

---

## Cross-Cutting Standards

Opaque sortable IDs · UTC storage · numeric money + currency · `actor_type` user|agent|system|webhook · idempotency keys · workspace_id on operational data

---

## Part 4 Closure

Logical enterprise data model baseline complete.  
**Deferred:** SQL, APIs, physical sizing, warehouse star-schema DDL.

---

**End of SRS Part 4 — Database Architecture**
