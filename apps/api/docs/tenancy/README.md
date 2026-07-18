# Multi-Tenant SaaS Foundation

Organization → Workspace → Membership isolation for CommerceAI OS.

## Hierarchy

```text
User (global identity)
  └── Organization (company)
        └── Workspace (operational tenant / workspace_id)
              └── Membership (role_code + status)
              └── Invitations
              └── Settings
```

## Modules

| Service | Responsibility |
|---------|----------------|
| OrganizationService | Create/update/soft-delete orgs + org settings |
| WorkspaceService | Multi-workspace CRUD + settings |
| MembershipService | Roles, suspend, remove, transfer ownership |
| InvitationService | Invite / accept / reject / revoke |
| ProfileService | User profile preferences |
| TenantAccessService | Boundary checks |

## Docs

- [Architecture](ARCHITECTURE.md)
- [Organizations](ORGANIZATIONS.md)
- [Workspaces](WORKSPACES.md)
- [Memberships & Invitations](MEMBERSHIPS.md)
- [Tenant Isolation](TENANT_ISOLATION.md)
