# SKU Management

## SKU rules

SKU handling is centralized in the catalog domain and validated through dedicated normalization and validation helpers.

## Behavior

- Input is normalized to uppercase and hyphenated form where appropriate.
- A SKU must pass validation before it can be persisted.
- Product default SKU and product variant SKU are both checked for uniqueness.

## Storage

SKU values are stored in:

- `products.default_sku`
- `product_variants.sku`
- `product_identifiers` for the `sku` identifier type

## Integrity expectations

The repository and service layers reject duplicate SKUs before commit.
