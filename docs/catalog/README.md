# Catalog & Product Management Foundation

This directory documents the internal enterprise catalog foundation for CommerceAI-OS.

## Scope

This foundation is limited to the internal source-of-truth catalog and does not include marketplace publishing, inventory synchronization, orders, pricing engines, or AI orchestration.

## Included domains

- Products
- Product variants
- SKU management
- Product identifiers
- Categories
- Tags and metadata
- Attributes and media
- Brand / manufacturer metadata
- Multi-tenant isolation

## Main implementation areas

- API routes: `apps/api/src/app/presentation/api/v1/routes/products.py`
- Application service: `apps/api/src/app/application/catalog/product_service.py`
- ORM models: `apps/api/src/app/infrastructure/persistence/models/catalog.py`
- Repositories: `apps/api/src/app/infrastructure/persistence/repositories/catalog.py`
- Domain rules: `apps/api/src/app/domain/catalog/`

## Related docs

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [PRODUCTS.md](PRODUCTS.md)
- [VARIANTS.md](VARIANTS.md)
- [SKU.md](SKU.md)
