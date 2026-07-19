# Listing Validation

`POST /listings/{id}/validate` runs:

1. Default completeness rules (title, description, price/qty, format, currency)
2. Optional eBay offline policy checks when `marketplace_type` is ebay

Blocking errors prevent submit-for-review and approve.
