# Catalog Architecture

## Layering

The catalog foundation follows the existing Clean Architecture and DDD conventions already used by the API project.

### Domain layer

The domain layer holds the catalog business language and invariants:

- product lifecycle transitions
- SKU normalization and validation
- identifier validation
- catalog exceptions and events

### Application layer

The application layer coordinates use cases such as:

- create product
- update product
- archive product
- restore product
- create variant
- update variant
- assign categories
- manage attributes
- manage media and identifiers

### Infrastructure layer

The infrastructure layer persists the model using SQLAlchemy ORM and async repositories. This layer enforces tenant-scoped queries and soft-delete filtering.

### Presentation layer

The HTTP API exposes CRUD-oriented endpoints for products, variants, identifiers, attributes, media, and categories.

## Aggregate boundaries

- Product aggregate
- Product variant aggregate
- Category aggregate
- Media / identifier records are owned by product and variant scopes

## Multi-tenant expectations

All product catalog access is tenant-scoped through the `X-Workspace-Id` header and the workspace access service.
