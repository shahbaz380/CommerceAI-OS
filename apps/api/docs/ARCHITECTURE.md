# Backend Architecture Overview

## Style

**Clean Architecture** + **Domain-Driven Design** + **SOLID** + constructor/DI composition root.

```text
presentation/     HTTP, middleware, schemas
application/      Use cases, ports (interfaces)
domain/           Entities, value objects, domain rules
infrastructure/   DB, Redis, Celery, AI/marketplace adapters, logging, OTEL
  database/       Engine, mixins, repositories, UoW
core/             Cross-cutting: DI, events, plugins, tenancy, security headers
bootstrap/        App factory + lifecycle
config/           Settings
tasks/            Celery tasks
```

## Dependency rule

```text
presentation → application → domain
       ↘         ↓
      infrastructure (adapters implement ports)
core/bootstrap wire the graph
```

Domain has **no** imports from FastAPI/SQLAlchemy.

## Persistence architecture

```text
┌─────────────────────────────────────────────┐
│              Application Services             │
└─────────────────────┬───────────────────────┘
                      │ UnitOfWork port
                      ▼
┌─────────────────────────────────────────────┐
│           SqlAlchemyUnitOfWork                │
│  commit / rollback / repository(Model)        │
└───────────┬─────────────────────┬───────────┘
            │                     │
            ▼                     ▼
   SqlAlchemyRepository     AsyncSession
            │                     │
            └──────────┬──────────┘
                       ▼
                 AsyncEngine
                       │
                       ▼
                  PostgreSQL
```

## Multi-tenant

- `TenantContext` on each request via `X-Workspace-Id` (foundation).  
- `TenantOwnedMixin.workspace_id` on tenant tables.  
- Repository auto-filters by workspace when scoped.  
- Future auth must bind workspace from membership claims.

## Async

- FastAPI async routes  
- SQLAlchemy async engine (`asyncpg`)  
- Redis asyncio client  
- Celery for background isolation  
- **No implicit IO lazy-loads** in async — use eager options

## Extensibility

| Concern | Extension point |
|---------|-----------------|
| Marketplaces | `MarketplaceRegistry` + `MarketplaceAdapter` |
| Plugins | `PluginLoader` + manifests |
| AI | `AIGateway` |
| Events | `EventBus` → future outbox |
| Persistence | New models + repos; UoW unchanged |
| Microservices | Extract adapters; keep ports |

## Request pipeline

```text
Client
  → TrustedHost / CORS / GZip
  → Security headers
  → Rate limit (placeholder)
  → RequestContext (IDs, tenant)
  → Access logging
  → Route → deps (UoW) → services
  → Exception handlers
```

## Configuration & secrets

- `AppSettings` loads env  
- Production rejects weak `SECRET_KEY` and `DEBUG=true`  
- `DATABASE_STARTUP_VALIDATE` / `STRICT` for boot checks  

## Observability

- structlog JSON  
- DB pool stats on `/health/ready` and `/health/database`  
- OTEL optional  
