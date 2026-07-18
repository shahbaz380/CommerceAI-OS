# Logging Strategy

**Version:** 1.0  

---

## Log Classes

| Class | Purpose | Destination (prod) | Local folder |
|-------|---------|-------------------|--------------|
| Application | Diagnostics, lifecycle | Central log stack | `logs/app` |
| API access | Request forensics | Central + metrics | `logs/api` |
| AI | Agent tasks, costs, safety | Central (redacted) | `logs/ai` / `ai/logs` |
| Security | Auth anomalies, denials | SIEM-capable store | `logs/security` |
| Infrastructure | Platform/node | Cloud provider logs | n/a |
| Business | Funnel/ops events | Analytics pipeline optional | `logs/business` |
| Audit | Who did what (compliance) | Immutable-ish store | `logs/audit` |

---

## Standard Fields

```text
timestamp, level, service, env, version,
requestId, correlationId, workspaceId,
actorType, actorId, eventCode, message,
durationMs?, errorCode?, stack? (server-only)
```

---

## AI Logs Specific

| Field | Notes |
|-------|-------|
| `agentCode` | e.g. `listing-optimization` |
| `taskId` | AI task id |
| `capabilityCode` | tool/capability |
| `promptVersion` | template version |
| `promptHash` | hash of rendered prompt |
| `confidence` | if recommendation |
| `riskTier` | L0–L4 |
| `tokenCostEst` | cost observability |
| `decisionId` | if approval-related |

Full prompt/response retention follows data retention policy (short for debug, longer for decisions/executions).

---

## Rotation & Retention (targets)

| Class | Hot retention | Cold archive |
|-------|---------------|--------------|
| Debug/app verbose | 7 days | optional |
| API access | 30 days | 90+ optional |
| Security | 90–365 days | longer if required |
| Audit | 1–7 years (policy) | yes |
| AI debug traces | 7–30 days | purge |
| AI decisions/exec | align with audit | yes |
| Business | 30–90 days | aggregate |

Exact days finalized in compliance workshop; implement as config.

---

## Rotation (local)

- Use size/time rotation for files under `logs/` when file transport enabled.
- Production prefers centralized shipping over large local disks.

---

## Rules

1. No secrets in logs.  
2. Prefer structured events over free-text only.  
3. Correlation IDs propagate API → worker → AI.  
4. Audit logs are append-only from app perspective.  
5. Tenant-scoped audit queries must enforce isolation.

---

**End of Logging Strategy**
