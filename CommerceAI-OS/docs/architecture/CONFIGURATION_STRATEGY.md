# Configuration Strategy

**Version:** 1.0  

---

## Principles

1. **Separate config from code**  
2. **Separate secrets from config**  
3. **Fail fast** on invalid config at process start (non-local)  
4. **Environment-specific overlays** without forking codebases  
5. **Feature flags** for risk control  

---

## Configuration Layers

```text
1. Code defaults (safe)
2. config/** committed templates (non-secret)
3. Environment-specific files (non-secret)
4. Process environment variables
5. Secret manager injection (runtime)
6. Dynamic feature flags (service/API later)
```

Higher layers override lower layers.

---

## Application Configuration

| Area | Location | Examples |
|------|----------|----------|
| App meta | `config/app/` | name, default locale |
| Environments | `config/environments/` | local/staging/production overlays |
| API | `config/api/` | timeouts, pagination defaults, CORS templates |
| Database | `config/database/` | pool sizes (non-password) |
| Logging | `config/logging/` | levels, redaction rules |
| Monitoring | `config/monitoring/` | exporter endpoints placeholders |
| AI | `config/ai/` | model routing templates, budgets |
| Feature flags | `config/feature-flags/` | default flag map |

---

## Secrets

| Secret class | Storage | Rotation |
|--------------|---------|----------|
| DB credentials | Secret manager | Scheduled + emergency |
| JWT signing keys | Secret manager | Controlled rotation |
| eBay OAuth client secrets | Secret manager | On provider schedule |
| LLM API keys | Secret manager | On leak/schedule |
| Stripe keys | Secret manager | Provider dashboard + store update |
| Webhook signing secrets | Secret manager | On rotate |

**Repo holds only:** `secrets/templates/*` and `secrets/policies/*`.

---

## Environment Variables

- Documented in `.env.example`
- Naming: `SCREAMING_SNAKE_CASE`
- Boolean flags: `true`/`false` lowercase
- URLs complete with scheme
- Never interpolate secrets into client-side bundles

---

## API Configuration

- Base path prefix `/api/v1`
- Request size limits
- Rate limit classes
- CORS allowlists per env
- Idempotency required routes list (when implemented)

---

## Database Configuration

- Connection string via `DATABASE_URL` or discrete parts
- Pool min/max per process type (api vs worker)
- SSL mode required in staging/production
- Migration connection may use separate role (future)

---

## Cloud Configuration

- Region, account, resource ARNs/names via env or SSM parameter store patterns
- No hardcoded account IDs in application libraries (inject at deploy)

---

## Logging Configuration

- `LOG_LEVEL`, `LOG_FORMAT=json|pretty`
- Redaction field lists in `config/logging/`
- Per-service overrides allowed

---

## Feature Flags

Default foundation flags (see `config/feature-flags/default.yaml`):

| Flag | Default | Intent |
|------|---------|--------|
| `FEATURE_AI_WRITES_ENABLED` | false | Kill/default off AI mutations |
| `FEATURE_EBAY_SYNC_ENABLED` | false | Sync not live until built |
| `FEATURE_BILLING_ENABLED` | false | Billing inactive until ready |
| `FEATURE_MULTI_CHANNEL_UI` | false | Single-channel UI first |

Flags must be readable by API and workers consistently (cache with short TTL later).

---

**End of Configuration Strategy**
