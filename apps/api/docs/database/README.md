# Database & Persistence Foundation

Enterprise persistence layer for CommerceAI OS API.

## Components

| Component | Location | Role |
|-----------|----------|------|
| Engine / sessions | `infrastructure/database/session.py` | Async engine, pool, health, lifecycle |
| Base models | `infrastructure/database/base.py` | Declarative Base + abstract model stacks |
| Mixins | `infrastructure/database/mixins/` | UUID, timestamps, soft delete, tenant, audit, version |
| Types | `infrastructure/database/types/` | GUID, EncryptedString |
| Repositories | `infrastructure/database/repositories/` | Generic async repository + specifications |
| Unit of Work | `infrastructure/database/uow/` | Transaction boundary |
| Alembic | `alembic/` | Migrations |
| Ports | `application/ports/` | UoW / repository protocols |

## Architecture

```text
Application Service
        │
        ▼
 SqlAlchemyUnitOfWork  ──session──►  PostgreSQL
        │
        ├── repository(ModelA)
        └── repository(ModelB)

ORM models inherit:
  AuditedTenantModel = UUID + timestamps + soft delete + workspace_id + audit + version
```

## Model inheritance (no business tables yet)

```text
Base
└── TimestampedModel          (id, created_at, updated_at)
    ├── SoftDeleteModel       (+ deleted_at)
    │   └── TenantModel       (+ workspace_id)
    │       └── AuditedTenantModel (+ created_by, updated_by, version)
    └── SystemModel           (non-tenant system catalogs)
```

## Guides

- [MIGRATIONS.md](MIGRATIONS.md)
- [REPOSITORY_GUIDE.md](REPOSITORY_GUIDE.md)
- [UNIT_OF_WORK_GUIDE.md](UNIT_OF_WORK_GUIDE.md)
- [BEST_PRACTICES.md](BEST_PRACTICES.md)

## Health

- `GET /health/ready` — DB + Redis  
- `GET /health/database` — version + pool stats  
