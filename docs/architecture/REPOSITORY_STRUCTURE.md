# CommerceAI OS — Repository Structure

**Version:** 1.0  
**Status:** Implementation Foundation  
**Date:** 2026-07-16  

This document explains **every major folder** in the monorepo: purpose, responsibilities, contents, guidelines, naming, and expansion.

> **Architecture stance:** *Microservice-ready modular monorepo.*  
> Start as a modular monolith inside `apps/*` + `packages/*`; extract `services/*` when scale or team boundaries require it. Marketplace connectors and plugins remain isolated from day one.

---

## Top-Level Map

```text
CommerceAI-OS/
├── apps/                 # Deployable applications
├── packages/             # Shared libraries (no deployables)
├── services/             # Optional extractable services / adapters
├── ai/                   # AI plane (orchestrator, agents, prompts, eval)
├── plugins/              # Installable capability plugins
├── database/             # Migrations, seeds, schema docs (no runtime secrets)
├── infrastructure/       # IaC, cluster, network definitions
├── deploy/               # Release/deploy blueprints per environment
├── config/               # Non-secret configuration templates
├── secrets/              # Templates & policies only (never real secrets)
├── security/             # Policies, threat models, cert/key placeholders
├── scripts/              # Developer & ops automation entrypoints
├── logs/                 # Local log output dirs (gitignored content)
├── monitoring/           # Dashboards, alerts, SLO definitions
├── tests/                # Cross-cutting test suites
├── tools/                # Dev tooling, generators, linters
├── assets/               # Static brand/media assets
├── docs/                 # All documentation (incl. SRS)
├── build/                # Build outputs (artifacts gitignored)
├── coverage/             # Coverage reports (gitignored)
├── sandbox/              # Local sandbox fixtures
├── tmp/                  # Scratch (gitignored)
├── .github/              # CI/CD, PR/issue templates
├── .vscode/ / .husky/    # Editor & git hooks (optional)
├── .env.example          # Env template
├── .gitignore
├── .editorconfig
└── README.md
```

---

## 1. `apps/`

### Purpose
Host **deployable runtime applications**.

### Responsibilities
- Own process entrypoints, HTTP servers, workers, schedulers, and UIs.
- Compose domain logic from `packages/*` and call adapters in `services/*`.
- Never embed long-lived secrets; read from environment/secret manager.

### Contents

| Path | Role |
|------|------|
| `apps/api/` | Primary public/internal HTTP API |
| `apps/web/` | Seller/operator web application |
| `apps/admin/` | Platform admin shell (visually distinct) |
| `apps/worker/` | Background job consumers |
| `apps/scheduler/` | Cron/schedule triggers |

Each app: `src/`, `tests/`, future `package.json` / Dockerfile (when stack is chosen).

### Development Guidelines
- One deployable unit per folder.
- Prefer thin apps: orchestration + wiring, logic in packages.
- No cross-app deep imports of private internals; use `packages/*` public APIs.

### Naming
- App folders: **kebab-case** (`apps/api`, `apps/web`).
- Entry files later: `main.ts` / `index.ts` / `server.ts` (stack-dependent).

### Future Expansion
- `apps/mobile/` BFF only if needed.
- Split `apps/api` into gateway + BFF without moving domain packages.

---

## 2. `packages/`

### Purpose
**Shared libraries** consumed by apps and services — versioned inside the monorepo.

### Responsibilities
- Stable, well-typed building blocks.
- Zero environment-specific secrets.
- High unit-test coverage expectations.

### Contents

| Package | Purpose |
|---------|---------|
| `shared` | Cross-cutting constants, result types |
| `types` | Domain & DTO TypeScript/JSON schema types |
| `config` | Config loading interfaces |
| `utils` | Pure utilities |
| `ui` | Shared design-system components (web/admin) |
| `sdk` | Internal client SDK for API consumers |
| `events` | Domain event names, envelopes, serializers |
| `logging` | Structured logger facade |
| `errors` | Error taxonomy / problem details |
| `auth-contracts` | Claims, permission code constants (no auth implementation yet) |
| `validation` | Shared validators / schemas |

### Guidelines
- Public exports only via package entrypoint.
- No importing from `apps/*`.
- Avoid circular dependencies; `types` and `errors` stay low in the graph.

### Naming
- Package folders: **kebab-case**.
- Package names (when published internally): `@commerceai/<name>`.

### Future Expansion
- `packages/tenancy`, `packages/money`, `packages/feature-flags` as needed.

---

## 3. `services/`

### Purpose
**Boundary-isolated services and integration adapters** — microservice-ready extraction points.

### Responsibilities
- Encapsulate external systems (marketplaces, billing, notifications).
- Translate external models ↔ canonical domain contracts.
- Own retry/rate-limit policy at the edge of the external API.

### Contents

| Path | Purpose |
|------|---------|
| `integration-ebay/` | eBay adapter (structure only now) |
| `integration-amazon/` … `integration-facebook/` | Future marketplace stubs |
| `notifications/` | Multi-channel notification dispatch service |
| `billing/` | Subscription/billing provider adapter |

### Guidelines
- **No business feature implementation yet** — folders + README stubs only until Phase 2+.
- Adapters must not leak provider SDKs into domain packages.
- Each integration gets its own tests folder.

### Naming
- `integration-<channel>` for marketplaces.
- Service code modules: kebab-case folders, clear `client`, `mapper`, `webhook` subareas later.

### Future Expansion
- Promote a service to a separately deployed process when team/scale requires; keep contract in `packages/`.

---

## 4. `ai/`

### Purpose
Entire **AI plane** foundation (no agent business logic yet).

### Responsibilities
- House orchestrator, agent packages, prompts, memory interfaces, knowledge base assets, model config, evaluation, AI logs, tools.

### Contents

| Path | Purpose |
|------|---------|
| `orchestrator/` | Planning, delegation, synthesis |
| `agents/*` | One folder per agent (A1–A10) |
| `prompts/library` | Curated prompt catalog metadata |
| `prompts/templates` | Versioned prompt templates |
| `memory/` | Memory port interfaces / local dev notes |
| `knowledge-base/` | Grounding documents (non-secret) |
| `models/config` | Model routing configuration templates |
| `evaluation/datasets` | Golden sets (non-PII) |
| `evaluation/harness` | Eval runner scaffolding (later) |
| `logs/` | Local AI log sink (gitignored content) |
| `tools/` | Tool registry definitions (schemas only later) |

### Guidelines
- Prompts are versioned artifacts; breaking prompt changes require eval.
- Agents never hold long-lived cloud credentials; use runtime secret injection.
- AI write paths must honor approval risk tiers (SRS Part 3).

### Naming
- Agent folders: **kebab-case** matching domain (`listing-optimization`).
- Prompt files: `v{major}.{minor}_{intent}.md` or `.json` (when added).

### Future Expansion
- Additional agents, multi-provider model configs, vector index adapters under `knowledge-base/`.

---

## 5. `plugins/`

### Purpose
**Plugin foundation** so future modules install without rewriting core.

### Responsibilities
- Define plugin contracts and registry.
- Isolate optional capabilities (marketplaces, accounting, CRM, etc.).

### Contents

| Path | Purpose |
|------|---------|
| `registry/` | Plugin manifest schema & discovery notes |
| `marketplace/` | Marketplace plugin pack umbrella |
| `accounting/` | Accounting integrations |
| `email-marketing/` | ESP plugins |
| `crm/` | External CRM plugins |
| `finance/` | Finance tooling plugins |
| `inventory-erp/` | ERP inventory bridges |

### Guidelines
- Plugins declare capabilities, permissions, risk tier, config schema.
- Core loads plugins via registry; core must not import plugin internals directly.
- Disabled by default until explicitly enabled per tenant/plan.

### Naming
- Plugin id: `plugin.<domain>.<provider>` (e.g. `plugin.marketplace.amazon`).

### Future Expansion
- Hot-pluggable packages, marketplace of internal plugins, version constraints.

---

## 6. `database/`

### Purpose
Schema evolution and data tooling artifacts **without** committing live data or secrets.

### Contents
`migrations/` · `seeds/` · `schemas/` (logical docs/export) · `scripts/` · `erd/`

### Guidelines
- Expand/contract migrations only.
- Seeds for local/dev only; never production PII.
- No SQL feature implementation in this foundation phase beyond folder readiness.

### Naming
- Migrations: `YYYYMMDDHHMMSS_description.sql` (or tool-native equivalent later).

---

## 7. `infrastructure/`

### Purpose
Infrastructure-as-code and platform definitions.

### Contents
`terraform/` · `kubernetes/` · `docker/` · `ansible/` · `scripts/` · `network/` · `modules/`

### Guidelines
- Separate state per environment.
- No plaintext secrets in IaC; use secret managers.
- Changes via PR + plan review.

### Naming
- Terraform modules: kebab-case; resources follow cloud provider conventions documented in deploy guides.

---

## 8. `deploy/`

### Purpose
**How** artifacts are released to environments (distinct from raw infra modules).

### Contents
`helm/` · `environments/` · `scripts/` · `blueprints/`

### Guidelines
- Environment overlays (staging/prod) live here.
- Production changes require approval gates (SRS Part 9).

---

## 9. `config/`

### Purpose
Non-secret configuration templates and defaults.

### Contents
`app/` · `environments/` · `feature-flags/` · `logging/` · `monitoring/` · `database/` · `api/` · `ai/`

### Guidelines
- Commit examples and schema; override with env-specific values outside git when sensitive.
- Feature flags default **safe** (AI writes off, marketplace sync off until built).

---

## 10. `secrets/`

### Purpose
**Templates and policies only.**

### Contents
`templates/` · `policies/`

### Guidelines
- Real secrets never committed (enforced by `.gitignore` + CI).
- Document rotation expectations in `secrets/policies/`.

---

## 11. `security/`

### Purpose
Security governance artifacts for the engineering org.

### Contents
`policies/` · `permissions/` · `certificates/` (placeholders) · `keys/` (placeholders) · `threat-models/` · `runbooks/`

### Guidelines
- Permission codes aligned with SRS RBAC.
- Threat models required for high-risk features before merge when applicable.

---

## 12. `scripts/`

### Purpose
Human- and CI-invoked automation entrypoints.

### Contents
`dev/` · `build/` · `db/` · `lint/` · `release/` · `bootstrap/` · `codegen/`

### Guidelines
- Scripts must be idempotent where possible.
- Document usage in `docs/developer/`.
- Prefer `scripts/bootstrap` for new machine setup (later).

### Naming
- `kebab-case.sh` or stack-native task names.

---

## 13. `logs/`

### Purpose
Local filesystem targets for log sinks during development.

### Contents
`app/` · `api/` · `ai/` · `security/` · `audit/` · `business/`

### Guidelines
- All log **content** gitignored; keep `.gitkeep`.
- Production logs go to centralized platforms (SRS Part 7–8).

---

## 14. `monitoring/`

### Purpose
Observability-as-code definitions.

### Contents
`dashboards/` · `alerts/` · `slo/` · `synthetic/` · `runbooks/`

### Guidelines
- Every page-worthy alert links a runbook.
- SLOs defined before GA (numeric targets in SRE workshop).

---

## 15. `tests/`

### Purpose
Cross-cutting test suites that span apps/packages.

### Contents
`unit/` · `integration/` · `e2e/` · `performance/` · `security/` · `ai-eval/` · `fixtures/` · `mocks/` · `contracts/` · `data/`

### Guidelines
- Prefer package/app colocation for unit tests; use `tests/` for cross-boundary suites.
- No production secrets in fixtures.
- Coverage standards in DEVELOPMENT_STANDARDS.md.

---

## 16. `tools/`

### Purpose
Developer experience tooling.

### Contents
`devcontainer/` · `generators/` · `linters/` · `formatters/` · `scripts/` · `devtools/`

---

## 17. `assets/`

### Purpose
Static brand and media assets for apps and docs.

### Contents
`brand/` · `icons/` · `images/` · `fonts/` · `templates/`

### Guidelines
- Optimize images; license compliance for fonts.
- Runtime user uploads go to object storage, not this folder.

---

## 18. `docs/`

### Purpose
All project documentation.

### Contents

| Path | Purpose |
|------|---------|
| `srs/` | Approved SRS Parts 1–10 |
| `architecture/` | Runtime & repo architecture |
| `api/` | OpenAPI & API guides (later) |
| `database/` | ERD narratives, retention |
| `ai/` | Agent & eval docs |
| `deployment/` | Deploy runbooks |
| `developer/` | Onboarding, standards |
| `user/` | End-user guides (later) |
| `admin/` | Platform admin guides |
| `security/` | Security program docs |
| `adr/` | Architecture Decision Records |
| `runbooks/` | Operational runbooks |
| `standards/` | Engineering standards |

---

## 19. `.github/`

### Purpose
CI/CD workflows, PR/issue templates.

### Contents
`workflows/ci.yml` (foundation checks) · `PULL_REQUEST_TEMPLATE.md` · `ISSUE_TEMPLATE/*`

### Future Expansion
- `cd-staging.yml`, `cd-prod.yml`, `security-scan.yml`, `ai-eval.yml` as code lands.

---

## 20. `build/`, `coverage/`, `tmp/`, `sandbox/`

| Folder | Purpose |
|--------|---------|
| `build/` | CI/local build artifacts (not committed) |
| `coverage/` | Coverage reports (not committed) |
| `tmp/` | Scratch space |
| `sandbox/` | Local sandbox data layouts for integrations |

---

## Dependency Direction (Allowed Imports)

```text
apps → packages, services (public API), ai (public API)
services → packages
ai → packages (not apps)
plugins → packages + plugin SDK (future)
packages → packages (acyclic; lower layers only)
```

**Forbidden:** `packages` → `apps`; `plugins` → `apps` internals; domain packages → concrete marketplace SDKs.

---

## Microservice Readiness

A folder under `services/*` or `apps/*` is extractable when it has:

1. Explicit API contract in `packages/` or OpenAPI  
2. Own datastore ownership boundary (if any)  
3. Own deployment unit definition under `deploy/`  
4. Isolated CI job  

Until then, run in-process modules with the same folder boundaries.

---

**End of Repository Structure Guide**
