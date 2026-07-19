# Listing API

Requires `Authorization` + `X-Workspace-Id`.

| Method | Path |
|--------|------|
| POST/GET | `/api/v1/listings` |
| GET/PATCH/DELETE | `/api/v1/listings/{id}` |
| POST | `.../validate`, `submit-for-review`, `approve`, `schedule`, `clone` |
| GET | `.../preview`, `.../versions` |
| CRUD | `/api/v1/listing-templates` |
| POST | `/api/v1/listings/{id}/apply-template/{template_id}` |
