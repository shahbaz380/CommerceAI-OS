# Unit of Work Guide

## Purpose

One **business transaction** per use case. Coordinates session lifecycle and commit/rollback.

## FastAPI dependency

```python
from app.presentation.api.deps import get_uow
from app.infrastructure.database.uow import SqlAlchemyUnitOfWork

@router.post("/example")
async def example(uow: SqlAlchemyUnitOfWork = Depends(get_uow)):
    repo = uow.repository(SomeModel)
    ...
    await uow.commit()
```

`get_uow` binds `workspace_id` from `RequestContext` when present.

## Semantics

| Action | Result |
|--------|--------|
| `async with uow` | Opens session |
| `await uow.commit()` | Commits transaction |
| Exception / no commit | Rollback on exit |
| `await uow.flush()` | Flush without commit |
| `uow.repository(Model)` | Tenant-scoped generic repository |

## Explicit commit

UoW **does not auto-commit** on success without `commit()` — prevents accidental partial writes.

## Nested work

Avoid nested UoW sessions for the same request; pass the same `uow` through application services.
