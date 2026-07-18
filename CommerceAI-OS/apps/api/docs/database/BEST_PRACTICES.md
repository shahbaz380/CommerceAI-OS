# Persistence Best Practices

## Multi-tenancy

- Every tenant table: `workspace_id` NOT NULL + index leading composites.  
- Repositories filter by tenant automatically when `workspace_id` set.  
- Never trust client headers alone once auth ships — derive tenant from membership.

## Soft delete

- Default reads exclude `deleted_at IS NOT NULL`.  
- Unique constraints often need partial indexes on active rows only.

## Optimistic locking

- On concurrent updates, SQLAlchemy raises `StaleDataError` when `version_id_col` is configured on the concrete mapper.  
- Map with `__mapper_args__ = {"version_id_col": VersionMixin.version}` on concrete models.

## Performance

- `pool_pre_ping=True`, recycle connections (`DATABASE_POOL_RECYCLE`).  
- Prefer keyset pagination for large lists (add to specialized repos).  
- Use `selectinload` for collections; avoid lazy IO in async (raises MissingGreenlet).  
- Index guidelines in `utils.INDEX_GUIDELINES`.

## Security

- `DATABASE_URL` only via env / secret manager.  
- SSL for staging/production (`postgresql+asyncpg` SSL query params / connect args as needed).  
- `EncryptedString` for tokens/secrets at rest (app-level); migrate to KMS envelope later.  
- Never log bound SQL with secrets (`database_echo` off in prod).

## Testing

- Use SQLite+aiosqlite in-memory for repository/UoW unit-integration tests.  
- Use real Postgres in CI for dialect-specific migrations.  
- Transaction rollback tests via UoW without commit.

## What not to put in this layer

- HTTP concerns  
- eBay / AI business rules  
- Authentication token issuance  
