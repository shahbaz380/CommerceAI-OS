# Product API

All product routes require `Authorization` and `X-Workspace-Id`.

| Method | Path |
|--------|------|
| POST/GET | `/api/v1/products` |
| GET/PATCH/DELETE | `/api/v1/products/{id}` |
| POST | `/api/v1/products/{id}/activate\|deactivate` |
| POST/PATCH | `/api/v1/products/{id}/variants...` |
| POST | `/api/v1/products/{id}/identifiers` |
| POST | `/api/v1/products/{id}/media` |
| POST | `/api/v1/product-categories` |
| GET | `/api/v1/product-categories/tree` |
