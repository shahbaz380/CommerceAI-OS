# Inventory Architecture

The inventory foundation remains aligned to the existing application architecture:

- Domain layer: value objects, enums, and validation errors
- Application layer: service orchestration for inventory, reservations, warehouses, transfers, and adjustments
- Persistence layer: SQLAlchemy async ORM models and repository abstractions
- Presentation layer: typed API schemas and FastAPI routes

The design intentionally stays internal to the enterprise workspace and does not introduce marketplace inventory synchronization.
