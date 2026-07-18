# Marketplace Architecture

## Patterns

| Pattern | Use |
|---------|-----|
| Adapter | `MarketplaceAdapter` per channel |
| Factory | `MarketplaceFactory` session-bound adapters |
| Registry | Channel discovery / health listing |
| Gateway | `MarketplaceGateway` / `EbayApiGateway` |
| Strategy | Retry/backoff policies on HTTP client |

## Component diagram

```text
API Routes (/marketplaces)
        │
        ▼
MarketplaceConnectionService / CredentialService
        │
        ├── TenantAccessService (workspace ACL)
        └── MarketplaceFactory
                │
                ├── EbayMarketplaceAdapter
                │     ├── EbayOAuthClient
                │     ├── EbayApiGateway
                │     └── Repositories (connections, tokens, states, logs)
                └── (future AmazonAdapter, ShopifyAdapter, ...)
                        │
                        ▼
                 AsyncHttpClient (retry, timeout, 429)
```

## OAuth flow

```text
Client                    API                         eBay
  |                        |                           |
  |-- POST credentials --->|                           |
  |-- POST connect ------->| create connection+state   |
  |<- authorization_url ---|                           |
  |---------------- browser redirect ----------------->|
  |<- code+state ----------|                           |
  |-- POST callback ------>| exchange code, store tokens
  |<- connected -----------|                           |
```

## Multi-tenant

All connections/credentials scoped by `workspace_id` with membership checks (manager/owner for mutations).
