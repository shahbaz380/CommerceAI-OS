# Products

## Product entity

The internal product record represents the parent catalog item used to group variants and identifiers.

## Supported fields

- name
- internal title
- description
- brand
- manufacturer
- model number
- product type
- condition
- status
- default SKU
- country of origin
- weight and dimensions
- tags
- metadata
- archived timestamp

## Lifecycle states

- draft
- active
- inactive
- archived
- deleted (soft delete)

## Notes

- A product can contain many variants.
- SKU uniqueness is enforced at the product and variant scope.
- Archived products are soft-deleted and can be restored through the restore flow.
