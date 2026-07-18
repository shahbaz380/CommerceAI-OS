# Tenant Isolation Strategy

## Layers

1. **AuthN** — JWT principal  
2. **Membership** — active workspace membership required for workspace APIs  
3. **Role rank** — owner > manager > staff > support > read_only  
4. **Header binding** — `X-Workspace-Id` validated against membership  
5. **Data** — future commerce tables use `TenantOwnedMixin.workspace_id`  
6. **Audit** — `tenant_audit_events` for lifecycle  

## Security rules

- Org owner always has access to all workspaces in org.  
- Cannot remove/demote last workspace owner.  
- Soft-delete orgs/workspaces (archive).  
- Invitation token stored hashed.  
