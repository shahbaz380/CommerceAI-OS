# Product Catalog Architecture

```text
API /products /product-categories
        │
        ▼
ProductService
        │
        ├── TenantAccessService
        ├── Product/Variant/Category/Media repositories
        └── Domain events (catalog.*)
```

Internal catalog is **marketplace-independent**. Listings reference `product_id` / `variant_id`.
