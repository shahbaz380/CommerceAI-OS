# RBAC Guide

## Model

```text
User ──< UserRole >── Role ──< RolePermission >── Permission
```

Global roles for now. **Workspace-scoped membership** arrives in Prompt 15.

## Permission checks (FastAPI)

```python
from app.presentation.api.deps.auth import require_permission, get_current_principal

@router.get("/x")
async def x(principal = Depends(require_permission("listing.read"))):
    ...
```

`Principal.is_superuser` bypasses permission checks.

## Seeding

`seed_identity_catalog(session)` runs on register/login and can be forced via:

`POST /api/v1/identity/seed` (requires `platform.admin`).

## Hierarchy

`hierarchy_rank` on roles (lower = higher privilege) for future comparative checks.
