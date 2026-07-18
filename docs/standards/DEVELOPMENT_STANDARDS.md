# CommerceAI OS — Development Standards

**Version:** 1.0  
**Status:** Mandatory for all contributors  
**Date:** 2026-07-16  

---

## 1. Folder Naming Convention

| Rule | Standard | Examples |
|------|----------|----------|
| Directories | `kebab-case` | `listing-optimization`, `integration-ebay` |
| Deployable apps | `kebab-case` under `apps/` | `apps/api` |
| Packages | `kebab-case` under `packages/` | `packages/auth-contracts` |
| Tests mirroring | Match source path | `tests/integration/orders/` |
| No spaces / underscores in new dirs | Prefer kebab-case | ~~`My_Module`~~ |

---

## 2. File Naming Convention

| Kind | Convention | Example |
|------|------------|---------|
| Source modules | `kebab-case.ts` / `.py` (stack TBD) | `price-calculator.ts` |
| React/Vue components (when added) | `PascalCase.tsx` | `OrderQueueTable.tsx` |
| Tests | `*.spec.*` or `*.test.*` | `price-calculator.spec.ts` |
| Config | `kebab-case.yaml` / `.json` | `feature-flags.default.yaml` |
| Migrations | timestamp + snake description | `20260716120000_add_workspaces.sql` |
| Docs | `SCREAMING_SNAKE` or `Title_Case` for standards; kebab for guides | `DEVELOPMENT_STANDARDS.md`, `getting-started.md` |
| Prompts | versioned | `v1.0_listing_title.json` |
| ADR | `NNNN-title.md` | `0001-modular-monolith.md` |

---

## 3. Variable Naming

| Language-agnostic rule | Style |
|------------------------|--------|
| Local variables | `camelCase` (TS/JS) or `snake_case` (Python) — **one language style per package** |
| Booleans | prefix `is`, `has`, `can`, `should` | `isActive`, `hasPermission` |
| Constants | `SCREAMING_SNAKE_CASE` | `MAX_PAGE_SIZE` |
| Env vars | `SCREAMING_SNAKE_CASE` | `DATABASE_URL` |
| Avoid | Single-letter names except loop indices; Hungarian notation |

---

## 4. Class / Type Naming

| Kind | Style |
|------|--------|
| Classes / Components | `PascalCase` | `InventoryService` |
| Interfaces / Types | `PascalCase`; avoid `I` prefix | `WorkspaceContext` |
| Enums | `PascalCase` enum; `SCREAMING_SNAKE` or `PascalCase` members (pick one per language) |
| Abstract ports | `PascalCase` + role | `ListingRepository`, `Clock` |
| DTOs | suffix `Dto` / `Dto` consistently | `CreateListingDto` |
| Errors | suffix `Error` | `TenancyViolationError` |

---

## 5. Function / Method Naming

| Kind | Style |
|------|--------|
| Functions/methods | `camelCase` (TS) / `snake_case` (Python) |
| Pure functions | verb or noun phrase | `calculateMargin`, `toCursor` |
| Event handlers | `on` / `handle` prefix | `onOrderCreated` |
| Factories | `create` / `make` | `createLogger` |
| Predicates | `is` / `has` | `hasActiveSubscription` |
| Async | no `Async` suffix noise unless overload conflict |

---

## 6. Environment Naming

| Env name | Purpose |
|----------|---------|
| `local` | Developer machine |
| `test` | Automated CI test runs |
| `qa` | Manual QA validation |
| `staging` | Pre-production, prod-like |
| `production` | Live tenants |
| `sandbox` | External provider sandboxes (eBay, Stripe test) |

**Variable:** `APP_ENV` (logical) distinct from `NODE_ENV`/`runtime env` when needed.

---

## 7. Configuration Standards

1. **12-factor style:** config via environment; secrets via secret manager.  
2. **Layering:** defaults (`config/`) < env file < process env < runtime secret inject.  
3. **Typed config:** validate at boot; fail fast on missing required keys in non-local.  
4. **No secrets in repo:** only `.env.example` and `secrets/templates/`.  
5. **Feature flags:** default safe; named `FEATURE_<AREA>_<ACTION>`.  
6. **Per-environment files:** `config/environments/{local,test,qa,staging,production}.yaml` (non-secret).  
7. **Document every new env var** in `.env.example` and developer docs.

---

## 8. Logging Standards

### Format
- **Structured JSON** in non-local environments.
- Required fields when available: `timestamp`, `level`, `service`, `env`, `requestId`/`correlationId`, `workspaceId`, `actorType`, `actorId`, `eventCode`, `message`.

### Levels
| Level | Use |
|-------|-----|
| `error` | Failures needing attention |
| `warn` | Recoverable anomalies |
| `info` | Significant business/ops events |
| `debug` | Diagnostic (disabled/sampled in prod) |
| `trace` | Extremely verbose (local only) |

### Rules
- **Never** log secrets, tokens, passwords, raw PAN, or full PII unnecessarily.
- Prefer IDs over names in logs.
- AI logs: store prompt **template version + hash**; retain full prompt bodies per retention policy only.
- Use event codes from a controlled vocabulary (`ORDER_TRACKING_SYNC_FAILED`).

---

## 9. Error Handling Standards

### Taxonomy (logical)
| Class | HTTP mapping (API) | Retryable |
|-------|--------------------|-----------|
| ValidationError | 400 | No |
| AuthenticationError | 401 | No |
| AuthorizationError | 403 | No |
| NotFoundError | 404 | No |
| ConflictError | 409 | Sometimes |
| BusinessRuleError | 422 | No |
| RateLimitError | 429 | Yes |
| DependencyError | 502/503 | Yes |
| InternalError | 500 | Sometimes |

### Rules
1. **Global exception filter** at API edge maps domain errors → stable problem details.  
2. Do not leak stack traces to clients.  
3. Include `code`, `message`, `details[]`, `retryable`, `requestId`.  
4. Wrap provider errors with platform codes + optional `providerCode` for ops.  
5. Prefer Result/Either patterns in domain cores for expected failures; throw for exceptional control flow only (language-idiomatic).  
6. **Idempotency:** retries of create/sync/AI execution must be safe.

---

## 10. Documentation Standards

| Doc type | Location | When required |
|----------|----------|---------------|
| ADR | `docs/adr/` | Cross-cutting or irreversible decisions |
| Module README | each major package/app | On package creation |
| API | `docs/api/` + OpenAPI | Any public endpoint |
| Runbook | `docs/runbooks/` or `monitoring/runbooks/` | Any pageable alert |
| SRS | `docs/srs/` | Approved baseline only; amend via change control |

**Style:** Markdown, descriptive titles, tables for matrices, no secrets, link to SRS parts by path.

---

## 11. Commenting Standards

- Prefer self-explanatory names over noise comments.
- Comments explain **why**, not what the next line does.
- Public package APIs: short doc comments.
- `TODO`/`FIXME` must include owner or ticket id.
- Do not comment out dead code; delete and rely on VCS.
- Security-sensitive algorithms may include reference links (e.g., threat model ADR).

---

## 12. Testing Standards (Foundation)

| Suite | Location | Expectation |
|-------|----------|-------------|
| Unit | colocated or `tests/unit` | Fast, isolated |
| Integration | `tests/integration` | Real DB/queue where practical |
| E2E | `tests/e2e` | Critical journeys |
| Contracts | `tests/contracts` | OpenAPI consumer/provider |
| Security | `tests/security` | Authz/tenancy |
| AI eval | `tests/ai-eval` + `ai/evaluation` | Golden sets |

**Coverage (targets when code exists):**
- Critical domain packages: **≥80%** line coverage aspirational; **100%** of tenancy/authz critical paths via explicit tests.
- No coverage gaming: prefer meaningful assertions.

---

## 13. Git Commit Message Convention

```text
<type>(<scope>): <short summary>

[optional body]

[optional footer]
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `security`

**Examples:**
```text
docs(standards): add development standards baseline
chore(repo): initialize monorepo foundation
feat(api): add health check endpoint
fix(tenancy): reject cross-workspace listing access
```

---

## 14. Versioning Strategy

| Artifact | Scheme |
|----------|--------|
| Product release | SemVer `MAJOR.MINOR.PATCH` |
| API | URI `/api/v{major}` |
| DB migrations | Monotonic sequence |
| AI prompts | `vMAJOR.MINOR` |
| Docker images (later) | `{semver}-{gitsha}` |

---

## 15. Security Baseline for Contributors

1. Never commit `.env` or keys.  
2. Run secret scanning mindset on every PR.  
3. Least privilege for new permissions.  
4. Tenancy checks are mandatory for multi-tenant resources.  
5. High-risk PRs require security-aware review (see Git strategy).

---

**End of Development Standards**
