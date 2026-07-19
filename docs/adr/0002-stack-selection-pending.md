# ADR 0002: Runtime Stack Selection

## Status

**Accepted** (2026-07-16) — supersedes pending status from foundation prompt.

## Context

Backend implementation requires a concrete runtime stack aligned with SRS (PostgreSQL, REST, multi-tenant SaaS, AI workers).

## Decision

| Layer | Choice |
|-------|--------|
| Language | **Python 3.12** |
| API framework | **FastAPI** |
| Validation | **Pydantic v2** |
| ORM | **SQLAlchemy 2.x (async)** |
| Migrations | **Alembic** |
| Cache / broker | **Redis** |
| Background jobs | **Celery** |
| Telemetry | **OpenTelemetry** |
| Tests | **Pytest** |
| Containers | **Docker** |
| Primary DB | **PostgreSQL** (unchanged from SRS) |

Web frontend stack remains deferred (separate ADR when UI implementation starts).

## Consequences

- Backend code lives primarily in `apps/api` with Clean Architecture packages.  
- Workers share the same codebase via Celery (`app.tasks`).  
- Type checking via mypy (strict mode configured).  
- Alternative stacks require a new ADR.  

## References

- `apps/api/README.md`  
- `apps/api/docs/ARCHITECTURE.md`  
- SRS Parts 4–5, 8  
