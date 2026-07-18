# Workspaces

Primary SaaS tenant boundary for future marketplace data.

## Endpoints

| Method | Path |
|--------|------|
| POST | `/api/v1/organizations/{org_id}/workspaces` |
| GET | `/api/v1/organizations/{org_id}/workspaces` |
| GET | `/api/v1/workspaces` |
| GET | `/api/v1/workspaces/current` |
| GET/PATCH/DELETE | `/api/v1/workspaces/{id}` |
| GET/PATCH | `/api/v1/workspaces/{id}/settings` |

## Switching

Send header: `X-Workspace-Id: <uuid>` with authenticated requests.
