# CommerceAI OS — Git Strategy

**Version:** 1.0  
**Date:** 2026-07-16  

---

## 1. Branch Model

```text
main
 │
 │  (release tags vX.Y.Z)
 │
develop ────────────────────────────── integration branch
 │
 ├── feature/<id>-short-description
 ├── fix/<id>-short-description
 ├── chore/<id>-short-description
 ├── docs/<id>-short-description
 │
 ├── release/x.y.0     (optional stabilization)
 │
 └── hotfix/x.y.z     (from main, merges to main + develop)
```

### 1.1 `main`

| Aspect | Rule |
|--------|------|
| Purpose | Production-ready history |
| Protection | Required reviews, required CI, no force-push |
| Deploy | Production (when CD exists) |
| Merge from | `release/*`, `hotfix/*`, or PR from `develop` when trunk-based simplified |

### 1.2 `develop`

| Aspect | Rule |
|--------|------|
| Purpose | Shared integration branch for ongoing development |
| Protection | Required CI; review recommended for all PRs |
| Deploy | Staging (when CD exists) |

### 1.3 Feature Branches

- Naming: `feature/<ticket>-kebab-summary`  
  Example: `feature/CAI-12-repo-foundation`
- Branch from: `develop`
- Merge to: `develop` via Pull Request
- Lifetime: short; delete after merge
- Scope: single concern; avoid mega-PRs

### 1.4 Release Branches

- Naming: `release/x.y.0`
- Branch from: `develop` when stabilizing a release
- Only bugfixes, version bumps, docs, release notes
- Merge to: `main` (tag) **and** back to `develop`

### 1.5 Hotfix Branches

- Naming: `hotfix/x.y.z`
- Branch from: `main`
- For production SEV fixes only
- Merge to: `main` (tag) **and** `develop`
- Requires accelerated review (dual approve for high risk)

---

## 2. Commit Message Convention

Follow Conventional Commits (see DEVELOPMENT_STANDARDS.md):

```text
type(scope): summary ≤ 72 chars

body (what/why)

BREAKING CHANGE: description
Fixes: #123
```

**Types:** feat, fix, docs, style, refactor, perf, test, build, ci, chore, security

**Scopes (examples):** `api`, `web`, `worker`, `ai`, `ebay`, `db`, `infra`, `ci`, `docs`, `security`, `repo`

---

## 3. Versioning Strategy

| Event | Version impact |
|-------|----------------|
| Backward-compatible feature | MINOR |
| Bugfix | PATCH |
| Breaking API/product change | MAJOR |
| Hotfix from prod | PATCH on main |

Tags: `v1.2.3` on `main`.  
API major versions independent via `/api/v1` (may lag product minor).

---

## 4. Pull Request Rules

1. PR template completed.  
2. Linked issue/ticket when applicable.  
3. CI green (`foundation-checks` now; expand later).  
4. At least **1 approving review** ( **2** for security/tenancy/payments/AI-write/migrations).  
5. No unresolved critical comments.  
6. Diff reasonably sized; split if > ~400 lines of logic without strong reason.  
7. No secrets in diff.  
8. Feature flags for risky behavior when applicable.  
9. Delete branch after merge.  
10. Squash or rebase merge policy: **squash preferred** for features; merge commits allowed for release trains if team prefers — pick one in ADR and keep consistent.

---

## 5. Code Review Workflow

```text
Author opens PR
    → CI runs
    → Reviewer(s) assigned by CODEOWNERS (when added)
    → Review for: correctness, tenancy, security, tests, standards, operability
    → Author addresses feedback
    → Approval
    → Merge to develop
    → (Later) release to main
```

### Reviewer checklist (abbreviated)

- [ ] Standards & naming  
- [ ] Tenancy/authz if multi-tenant data  
- [ ] Error/logging quality  
- [ ] Tests adequate for risk  
- [ ] Docs/ADR if contract change  
- [ ] Rollback possible  

### CODEOWNERS (to add when GitHub team exists)

Suggested future paths:

```text
/security/ @security-team
/ai/ @ai-leads
/database/ @data-leads
/.github/ @platform-leads
```

---

## 6. Protected Branch Settings (Recommended)

| Setting | `main` | `develop` |
|---------|--------|-----------|
| Require PR | Yes | Yes |
| Require status checks | Yes | Yes |
| Require linear history | Optional | Optional |
| Restrict force push | Yes | Yes |
| Restrict deletions | Yes | Yes |

---

## 7. Hotfix Workflow Detail

1. Declare SEV if production impact.  
2. Branch `hotfix/*` from `main`.  
3. Minimal fix + tests.  
4. Accelerated review.  
5. Merge to `main`, tag, deploy.  
6. Merge back to `develop` immediately.  
7. Post-incident follow-up if SEV-1/2.

---

**End of Git Strategy**
