# Applications

Deployable units:

| App | Role | Status |
|-----|------|--------|
| `api` | HTTP API (FastAPI) | **Foundation implemented** |
| `web` | Seller/operator UI | Scaffold only |
| `admin` | Platform admin UI | Scaffold only |
| `worker` | Async job consumers | Use Celery via apps/api for now |
| `scheduler` | Scheduled triggers | Scaffold only |

See `apps/api/README.md` for backend foundation details.
