# CommerceAI OS — Development Environments

**Version:** 1.0  

---

## Environment Overview

| Environment | Purpose | Data | External systems | Stability |
|-------------|---------|------|------------------|-----------|
| **Local** | Individual developer coding & debugging | Synthetic / empty / local containers | Mocks or provider sandboxes | Volatile |
| **Test** | Automated CI pipelines | Ephemeral seeded fixtures | Mocks; occasional sandbox | Ephemeral |
| **QA** | Manual exploratory & acceptance by QA | Anonymized or synthetic | Sandboxes | Shared, resettable |
| **Staging** | Prod-like validation, UAT, release candidate | Near-prod shape; no real customer secrets | Provider **sandbox/test** modes | Stable between releases |
| **Production** | Live tenants | Real tenant data | Live providers | Highest change control |
| **Sandbox** | Isolated integration experiments with marketplaces/AI | Disposable | Explicit sandbox credentials | On-demand |

> **Note:** `APP_ENV=sandbox` may also label a **mode** for marketplace APIs inside local/staging (eBay sandbox). The `sandbox/` repo folder holds local fixtures, not cloud accounts.

---

## Local Development

**Purpose:** Fast feedback loop for engineers.

**Characteristics:**
- `.env` from `.env.example`
- Optional docker-compose later for Postgres/Redis
- Feature flags: AI writes off, eBay sync off by default
- Logs to `logs/*` and console

**Must not:** use production secrets or production marketplace apps.

---

## Testing (`test`)

**Purpose:** CI unit/integration/contract suites.

**Characteristics:**
- Ephemeral databases
- Deterministic seeds from `tests/fixtures` and `tests/data`
- Parallel-safe tests
- No dependency on developer laptops

---

## QA

**Purpose:** Human QA validation of builds from `develop` or release candidates.

**Characteristics:**
- Shared QA deployment
- Reset scripts allowed
- Test accounts with known roles (Owner, Manager, Staff, Viewer)
- Bug reproduction environment

---

## Staging

**Purpose:** Production-like dress rehearsal.

**Characteristics:**
- Multi-AZ optional but topology mirrors prod (SRS Part 8)
- Separate AWS account/project recommended
- Marketplace **sandbox** credentials only
- UAT and pilot rehearsals
- Same security controls as prod where practical

---

## Production

**Purpose:** Serve real customers.

**Characteristics:**
- Protected deploys, approvals, canary
- Real secrets in secret manager
- Full monitoring, backups, on-call
- Feature flags for progressive delivery

---

## Sandbox (Integration)

**Purpose:** Safe experimentation with eBay/Stripe/LLM sandboxes without touching staging data.

**Characteristics:**
- Disposable workspaces
- Higher log verbosity
- Cost caps mandatory for AI

---

## Promotion Flow

```text
Local → PR → Test (CI) → develop → QA / Staging → main → Production
                              ↘ sandbox experiments (isolated)
```

---

**End of Environments Guide**
