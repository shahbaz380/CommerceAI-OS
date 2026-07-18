# Backend Developer Guide

## Setup

1. Python 3.12+  
2. `cd apps/api && python -m venv .venv && source .venv/bin/activate`  
3. `pip install -e ".[dev]"`  
4. `cp .env.example .env`  
5. `docker compose up -d` (Postgres + Redis)  
6. `export PYTHONPATH=src`  
7. `uvicorn app.main:app --reload --app-dir src`  
   or `PYTHONPATH=src uvicorn app.main:app --reload`

## Project layout mental model

Implement features **outside** foundation carefully:

1. Domain types in `domain/<context>/`  
2. Ports in `application/ports/`  
3. Use cases in `application/services/`  
4. SQLAlchemy models/repos in `infrastructure/database/` (next phase)  
5. HTTP in `presentation/api/v1/routes/`  
6. Wire in `core/di/container.py` if new infra services  

## Running tests

```bash
cd apps/api
export PYTHONPATH=src APP_ENV=testing
pytest -q
```

## Adding a middleware

1. Implement under `presentation/middleware/`  
2. Register in `registration.py` with correct order  
3. Add unit/integration coverage  

## Adding a Celery task

1. Module under `app/tasks/`  
2. Ensure included via Celery `include`  
3. Use JSON-serializable payloads only  
4. Prefer idempotent task design  

## Configuration

- Prefer new settings fields on `AppSettings`  
- Document in `.env.example`  
- Never commit secrets  

## Health probes

| Endpoint | Use |
|----------|-----|
| `/health/live` | K8s liveness |
| `/health/ready` | K8s readiness (DB+Redis) |
| `/health` | Shallow OK |
| `/health/version` | Version |
| `/health/system` | Ops diagnostics |

Also mounted under `/api/v1/...`.
