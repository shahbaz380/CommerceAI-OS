# Listing Architecture

```text
Product (catalog) ──< Listing >── MarketplaceConnection (optional)
                      │
                      ├── ListingContent
                      ├── ListingVersion
                      ├── ListingValidationResult/Issues
                      ├── ListingStatusHistory
                      └── ListingMarketplaceMapping
```

Validation uses Strategy/Registry:

- `DefaultListingValidator`
- `EbayListingPolicyValidator` (offline policy checks only)
