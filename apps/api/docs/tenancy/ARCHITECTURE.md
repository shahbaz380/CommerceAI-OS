# Tenancy Architecture

```text
API Routes (/organizations, /workspaces, /profiles)
        │
        ▼
Application services (tenancy/*)
        │
        ├── TenantAccessService (authz boundaries)
        └── Repositories → SQLAlchemy models
                │
                ▼
         PostgreSQL (workspace_id tenant key for future commerce rows)
```

## Tenant resolution

1. Authenticate user (JWT).  
2. Optional `X-Workspace-Id` header.  
3. `resolve_active_tenant` validates active membership.  
4. Binds `TenantContext(workspace_id, company_id=organization_id)`.  

Future commerce repositories filter by `workspace_id` from this context.
