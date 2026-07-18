# Backend Coding Standards (Python)

Extends monorepo `docs/standards/DEVELOPMENT_STANDARDS.md`.

## Python style

- Python 3.12+ syntax (`list[str]`, `X | None`)  
- Ruff for lint; format with ruff format / black-compatible  
- Type hints on public functions  
- `async def` for I/O-bound FastAPI paths  

## Architecture rules

1. Domain layer: pure Python, no FastAPI/SQLAlchemy imports.  
2. No business logic in routes — routes orchestrate use cases only.  
3. Prefer explicit dependencies via `Depends` + container.  
4. Raise `AppError` subclasses for expected failures.  
5. Log with structlog bound context; never log secrets.  

## Multi-tenancy

- Every query/filter for tenant data must include `workspace_id` (when models exist).  
- Never trust client workspace header alone after auth is implemented.  

## Testing

- Unit tests for pure logic and handlers  
- Integration tests for DB/Redis when available  
- Name tests `test_<behavior>`  

## Commits

Conventional Commits, e.g. `feat(api): add health readiness checks`.
