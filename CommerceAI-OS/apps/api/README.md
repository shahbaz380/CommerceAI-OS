# CommerceAI OS — Backend API (`apps/api`)

Enterprise **FastAPI** backend foundation using **Clean Architecture + DDD**.

| Item | Value |
|------|--------|
| Python | 3.12+ |
| Framework | FastAPI |
| ORM | SQLAlchemy 2.x (async) |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Queue | Celery + Redis |
| Cache | Redis |
| Telemetry | OpenTelemetry (optional) |
| Tests | Pytest |

## What is implemented (foundation)

- Application factory + lifespan bootstrap  
- Typed configuration (`AppSettings`) for local/dev/test/staging/production  
- Structured logging (structlog JSON/console)  
- DI container (`AppContainer`)  
- Middleware: request/correlation IDs, access logs, security headers, CORS, GZip, rate-limit placeholder  
- Global exception handlers with stable problem details  
- Health endpoints: `/health`, `/health/live`, `/health/ready`, `/health/version`, `/health/system`, `/health/database`  
- **Persistence layer:** async engine, pool monitoring, mixins, generic repository, Unit of Work, Alembic baseline  
- Redis client wrapper  
- Celery app + sample `ping` task  
- Event bus, plugin loader, AI gateway placeholder, eBay adapter placeholder  
- OpenTelemetry setup hook  

## Identity (Prompt 14)

See [docs/identity/README.md](docs/identity/README.md).

- Auth: register, login, logout, refresh, sessions, password change  
- RBAC: roles, permissions, `require_permission` deps  
- Security: Argon2, JWT, lockout, audit events  
- OAuth: provider framework only (no live IdPs)

## Multi-tenant SaaS (Prompt 15)

See [docs/tenancy/README.md](docs/tenancy/README.md).

- Organizations, workspaces, memberships, invitations  
- Profiles & org/workspace settings  
- Tenant resolver via `X-Workspace-Id`  
- Tenant audit events  

## Marketplace foundation (Prompt 16)

See [docs/marketplaces/README.md](docs/marketplaces/README.md).

- Marketplace adapter/factory/registry framework  
- eBay OAuth connect/refresh/disconnect  
- Encrypted credentials & tokens  
- HTTP gateway with retry/rate-limit  
- Webhook receiver foundation  

## What is NOT implemented

- Business tables (orders, listings, inventory, …)  
- Business marketplace resource APIs (listings/orders sync)  
- AI agent logic  

## Persistence docs

See [docs/database/README.md](docs/database/README.md).  

## Quick start

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env

# Optional local deps
docker compose up -d

export PYTHONPATH=src
uvicorn app.main:app --reload --port 8000
```

Open:

- http://localhost:8000/health/live  
- http://localhost:8000/docs (if docs enabled)  

## Tests

```bash
cd apps/api
pip install -e ".[dev]"
export PYTHONPATH=src
pytest -q
```

## Package map

See [docs/FOLDER_GUIDE.md](docs/FOLDER_GUIDE.md) and monorepo [REPOSITORY_STRUCTURE](../../docs/architecture/REPOSITORY_STRUCTURE.md).

## Architecture docs

- [ARCHITECTURE.md](docs/ARCHITECTURE.md)  
- [DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md)  
- [CODING_STANDARDS.md](docs/CODING_STANDARDS.md)  
