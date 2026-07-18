# Memberships & Invitations

## Members

| Method | Path |
|--------|------|
| GET | `/workspaces/{id}/members` |
| PATCH | `/workspaces/{id}/members/{user_id}` |
| POST | `.../suspend` |
| DELETE | `.../members/{user_id}` |
| POST | `/workspaces/{id}/transfer-ownership` |

## Invitations

| Method | Path |
|--------|------|
| POST | `/workspaces/{id}/invitations` (returns one-time `token`) |
| GET | `/workspaces/{id}/invitations` |
| POST | `/invitations/accept` |
| POST | `/invitations/reject` |
| DELETE | `/invitations/{id}` |

Email delivery is not wired — token returned in API for now.
