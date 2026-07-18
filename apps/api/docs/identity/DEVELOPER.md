# Identity Developer Guide

## Run migrations

```bash
cd apps/api
export PYTHONPATH=src
alembic upgrade head
```

## Protect a route

```python
from app.presentation.api.deps.auth import require_permission

@router.post("/publish")
async def publish(user=Depends(require_permission("listing.publish"))):
    ...
```

## Auth service (application layer)

```python
auth = AuthService(session)
result = await auth.login(email=..., password=...)
```

## Tests

```bash
pytest tests/unit/identity tests/integration/identity -q
```

## Adding a permission

1. Add to `PermissionCode` + `SYSTEM_PERMISSIONS`  
2. Grant in `role_permission_map()`  
3. Re-seed catalog  
