# Repository Pattern Guide

## Purpose

Isolate data access from application services. All queries for an aggregate go through a repository.

## Usage

```python
async with SqlAlchemyUnitOfWork(session_factory, workspace_id=ws) as uow:
    repo = uow.repository(MyModel)
    entity = await repo.get_or_raise(entity_id)
    entity.name = "updated"
    await uow.commit()
```

## Generic API

| Method | Behavior |
|--------|----------|
| `get` / `get_or_raise` | By UUID; respects soft-delete + tenant filters |
| `list` / `count` | Pagination (max 500); optional Specification |
| `add` / `add_many` | Insert + flush; tenant mismatch → ConflictError |
| `delete` | Soft by default if mixin present; `hard=True` hard delete |
| `restore` | Clears `deleted_at` |

## Specifications

Compose filters:

```python
spec = TenantIdSpec(ws) & NotDeletedSpec()  # usually automatic
rows = await repo.list(specification=MyCustomSpec(...))
```

## Rules

1. Do not use the session for ad-hoc queries in application services when a repository exists.  
2. Always pass `workspace_id` for tenant models.  
3. Prefer `selectinload` helpers in specialized repositories for aggregate graphs.  
4. Keep repositories free of HTTP / FastAPI types.  
