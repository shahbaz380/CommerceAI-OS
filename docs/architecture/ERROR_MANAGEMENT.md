# Error Management Strategy

**Version:** 1.0  

---

## Global Exception Handling

- Single API edge mapper converts domain/application errors → stable HTTP problem documents.
- Workers convert errors → structured job failure results + metrics (no HTTP).
- Unhandled errors: log at `error` with stack (server-side), return generic 500 to clients.

---

## Error Categories

### Validation Errors
- Schema/field failures  
- HTTP 400  
- `details[]` with field paths  

### Business Errors
- State machine violations, min profit, entitlement limits  
- HTTP 422  
- Stable `code` for client branching  

### API Errors
- Authn 401, authz 403, not found 404, conflict 409, rate limit 429  

### AI Errors
| Subtype | Handling |
|---------|----------|
| Provider timeout | Retryable DependencyError; degrade UX |
| Safety block | Non-retryable; user-safe message |
| Low confidence | Not an exception — route to human triage |
| Budget exceeded | 429/422 business code `AI_BUDGET_EXCEEDED` |
| Schema validation fail on model output | Retry once with repair prompt or fail task |

### Database Errors
- Unique violations → ConflictError  
- Deadlocks → retryable with backoff  
- Connection exhaustion → DependencyError + alert  

---

## Retry Strategy

| Condition | Policy |
|-----------|--------|
| Transient network/5xx from deps | Exponential backoff + jitter |
| HTTP 429 | Honor Retry-After |
| Validation/business 4xx | Never retry blindly |
| Jobs | Max attempts → DLQ |
| AI cost-heavy calls | Bounded retries (≤1–2) |

Idempotency keys required for payment, sync upsert, AI execution side effects.

---

## Client Error Contract (logical)

```text
{
  "code": "STRING_STABLE",
  "message": "Human safe message",
  "details": [{ "field": "...", "issue": "..." }],
  "retryable": false,
  "requestId": "..."
}
```

---

**End of Error Management**
