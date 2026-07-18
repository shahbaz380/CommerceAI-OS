# Backend Folder Guide

Root: `apps/api/`

| Path | Purpose | Responsibilities |
|------|---------|------------------|
| `src/app/bootstrap/` | App factory & lifecycle | Create FastAPI app, startup/shutdown |
| `src/app/config/` | Configuration | Env loading, validation, feature flags |
| `src/app/core/di/` | Dependency injection | Composition root / container |
| `src/app/core/events/` | Domain events | In-process bus |
| `src/app/core/plugins/` | Plugin system | Manifest registration/load |
| `src/app/core/security/` | Security helpers | Headers (auth later) |
| `src/app/core/tenancy/` | Multi-tenant | Header → TenantContext |
| `src/app/domain/*/` | Domain layer | Entities per bounded context (stubs) |
| `src/app/application/` | Application layer | Ports, DTOs, use cases (stubs) |
| `src/app/infrastructure/database/` | Persistence engine | Async engine/session, Base |
| `src/app/infrastructure/cache/` | Redis | Cache client |
| `src/app/infrastructure/messaging/` | Celery | Broker config |
| `src/app/infrastructure/logging/` | Logging | structlog setup |
| `src/app/infrastructure/monitoring/` | Telemetry | OpenTelemetry |
| `src/app/infrastructure/ai/` | AI gateway | Placeholder |
| `src/app/infrastructure/marketplace/` | Channel adapters | eBay placeholder + registry |
| `src/app/presentation/api/` | HTTP API | Routes, deps, errors |
| `src/app/presentation/middleware/` | Middleware | IDs, logs, security, CORS stack |
| `src/app/presentation/schemas/` | API schemas | Pydantic response models |
| `src/app/shared/` | Shared kernel | Exceptions, utils, validators, types |
| `src/app/tasks/` | Celery tasks | Background jobs |
| `src/app/workers/` | Worker helpers | Process entry later |
| `alembic/` | Migrations | Env ready; no table revisions yet |
| `tests/` | Pytest | Unit/integration/e2e folders |
| `docs/` | Backend docs | Architecture & guides |
| `docker-compose.yml` | Local deps | Postgres + Redis |
| `Dockerfile` | Container image | Runtime API |
| `pyproject.toml` | Packaging | Dependencies & tool config |

## Naming

- Packages/modules: `snake_case`  
- Classes: `PascalCase`  
- Env vars: `SCREAMING_SNAKE_CASE`  
- Aligns with monorepo `docs/standards/DEVELOPMENT_STANDARDS.md`  
