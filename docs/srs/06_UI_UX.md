# Software Requirements Specification (SRS) — Part 6
## CommerceAI OS – Frontend, Dashboard, UI/UX Architecture

**Document Version:** 1.0  
**Status:** Frontend & UX Architecture Baseline  
**Date:** 2026-07-16  
**Predecessors:** Parts 1–5  

---

### Document Control

| Field | Value |
|--------|--------|
| Document Part | Part 6 — Frontend, Dashboard, UI/UX |
| Excluded | Source code, HTML/CSS/JS/React implementation, pixel mock binaries |
| Next Part | Part 7 — Security, DevOps & Infrastructure |

---

# SECTION 1 — Frontend Vision

**Philosophy:** Professional operations cockpit — glanceable status → prioritized work → assisted action → confirmed outcome.

| Principle | Application |
|-----------|-------------|
| User-centered | Jobs-to-be-done; role-based density |
| Simplicity | One primary action; progressive disclosure |
| Performance | Skeletons; async jobs; freshness honesty |
| Accessibility | WCAG 2.2 AA baseline |
| Responsive | Desktop primary for bulk ops; mobile for monitor/respond |
| Themes | Light / Dark / System; semantic tokens |

---

# SECTION 2 — User Roles

| Role | Default home | Scope |
|------|--------------|-------|
| Super Admin | System Health (admin shell) | Cross-tenant break-glass, platform ops |
| Company Owner | Profit-aware dashboard | Full ops + billing + connect/disconnect |
| Team Manager | Operations dashboard | Broad ops; limited billing |
| Staff Member | My Work Queue | Queues: orders, messages, limited bulk |
| Read-Only | Analytics/KPI view | No mutations; AI Q&A only |

Navigation, modules, and restrictions follow RBAC and entitlements (see Part 2 matrices).

---

# SECTION 3 — Global Layout

```text
TOP: Logo | Workspace switcher | Quick Search | Sync chip | Lang | Theme | AI | Bell | Profile
LEFT: Collapsible sidebar (Overview, Commerce, Customers, Intelligence, Growth, System)
MAIN: Route canvas
RIGHT: Optional Notifications / AI mini / Entity peek
FOOTER: Compact help/status/version
```

**Quick Search:** `Cmd/Ctrl+K` omnibar (entities + commands)  
**AI Button:** Workbench entry; approval badge  
**Profile:** Security, prefs, sign out, billing shortcut (owner)

---

# SECTION 4 — Dashboard Widgets

Today’s Sales · Orders · Revenue · Profit (with quality badge) · Inventory · Low Stock · AI Recommendations · Latest Messages · Recent Activity · Notifications · Performance Graphs · Business Health Score · Quick Actions  

Role-default layouts; last-sync on each widget; click-through to modules.

---

# SECTIONS 5–14 — Module Screens (Design Intent)

## Listings
Dashboard · Create · Edit · Bulk Edit wizard · Drafts · SEO Score · Image Manager · History · Job progress/results

## Inventory
Dashboard · Stock Detail · Supplier Inventory · Timeline · Alerts · Forecast charts · Policies/thresholds

## Pricing
Monitor · Rules · Profit rules · Competitors · Recommendations · History · Bulk wizard · Apply jobs

## Orders
Dashboard · Pending/Completed/Cancelled · Detail · Shipment tracking · Bulk tracking · Refunds · Returns

## Support
Inbox (split view) · Conversation · AI reply suggestions (insert ≠ send) · Tickets · Refund workflow · Complaint analysis

## AI Assistant
Conversations rail · Chat thread · Suggested prompts · Recommendations · **Approvals** · Task history · Insights · Voice-ready affordance

## Analytics
Home · Revenue/Sales/Profit/Expenses/ROI · Customer/Supplier analytics · Export Center

## Guest CRM
Clients · Vendors · Websites · Deals (board+table) · Campaigns · Email tracking · Performance dashboard

## Blog & SEO
Blog dashboard · Articles/editor · Keyword center · SEO scores · Content calendar · Internal linking

## Settings
Profile · Business · Workspace · Members · Security · Sessions · Notifications matrix · Connections (eBay wizard) · API keys · Subscription · Billing · Automation/autonomy policies

## Admin Panel (distinct shell)
System Health · Users · Subscriptions · Logs · AI Usage · Monitoring · Error Center · Audit Logs

## Notifications
In-app panel · Full history · Channel coachmarks · Preference matrix (event × channel)

---

# SECTION 16 — UI Components

Buttons · Cards · Tables (server-paginated) · Forms · Charts · Dialogs · Drawers · Tabs · Dropdowns · Filters · Pagination · Skeletons · Toasts · Empty states  

**Cross-cutting:** Job progress · Sync freshness badge · Permission tooltips · Data quality badge · Risk tier badge · Channel icons

---

# SECTION 17 — UX

**Journeys:** Onboarding connect→sync · Morning ops · Catalog bulk · Margin defense approval · Support AI draft · Reauth recovery  

**A11y:** Keyboard, focus, contrast, live regions, chart alternatives  
**Onboarding checklist:** Connect · Import · Locale · Low stock · Invite · Try AI draft  
**Help:** Contextual help, shortcuts sheet (`?`)

---

# SECTION 18 — Multi-Channel UI Expansion

Stable shell + channel switcher/badges + dynamic channel attribute panels. No per-marketplace clone of entire IA. Amazon/Shopify/Walmart/Woo/TikTok/Facebook added via connection cards and capability flags.

---

# Screen Inventory Summary

Approximately **~155** distinct screens/wizards/admin views across auth, commerce, AI, growth, settings, and admin (full catalog maintained in project planning; hierarchy in Part 10).

**Priority bands:** P0 MVP spine → P1 daily ops → P2 pricing/support/analytics → P3 SEO/CRM → P4 admin/advanced

---

## Part 6 Closure

Enterprise frontend/UX baseline complete.  
**Deferred:** Visual brand kit, component library code, framework selection detail, Part 7.

---

**End of SRS Part 6 — Frontend & UI/UX Architecture**
