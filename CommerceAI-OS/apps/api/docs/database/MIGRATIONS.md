# Alembic Migration Guide

## Layout

```text
apps/api/
  alembic.ini
  alembic/
    env.py              # async migrations, Base.metadata
    script.py.mako
    versions/
      20260716_0001_persistence_foundation.py
```

## Workflow

### 1. Add / change ORM models

Place models under a persistence models package (future) and **import them in `alembic/env.py`** so metadata is complete.

### 2. Autogenerate (when models exist)

```bash
cd apps/api
export PYTHONPATH=src
alembic revision --autogenerate -m "add_workspaces"
```

Review the generated file carefully (autogenerate is not perfect).

### 3. Apply

```bash
alembic upgrade head
```

### 4. Rollback one step

```bash
alembic downgrade -1
```

### 5. History

```bash
alembic history
alembic current
```

## Rules

1. **Expand/contract** — prefer additive columns; avoid destructive changes without multi-step deploy.  
2. **Never** edit applied migrations on shared branches — add a new revision.  
3. Name files `YYYYMMDD_HHMM_<slug>.py` or sequential ids.  
4. PostgreSQL-specific SQL must be dialect-guarded if tests use SQLite.  
5. Foundation revision `20260716_0001` enables `pgcrypto` on PostgreSQL only.

## Offline SQL

```bash
alembic upgrade head --sql > /tmp/migration.sql
```

## CI

Run `alembic upgrade head` against ephemeral Postgres in integration pipelines (future job).
