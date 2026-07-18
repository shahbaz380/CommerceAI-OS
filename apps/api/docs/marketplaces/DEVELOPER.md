# Marketplace Developer Guide

## Add a new marketplace

1. Implement `MarketplaceAdapter` under `infrastructure/marketplace/<channel>/`.  
2. Register in `MarketplaceFactory.create`.  
3. Add channel enum value if new.  
4. Reuse `AsyncHttpClient` + `BaseMarketplaceGateway`.  
5. Add tests with `httpx.MockTransport`.  

## Key APIs

| Method | Path |
|--------|------|
| GET | `/api/v1/marketplaces/channels` |
| POST/GET | `/api/v1/marketplaces/workspaces/{id}/credentials` |
| GET | `/api/v1/marketplaces/workspaces/{id}/connections` |
| POST | `/api/v1/marketplaces/workspaces/{id}/connect` |
| POST | `/api/v1/marketplaces/workspaces/{id}/connect/callback` |
| POST | `.../connections/{id}/disconnect` |
| POST | `.../connections/{id}/refresh` |
| GET | `.../connections/{id}/validate` |
| GET | `.../connections/{id}/health` |
| POST | `/api/v1/marketplaces/webhooks/{channel}` |

## Migration

```bash
alembic upgrade head  # includes 20260716_0004_marketplace_tables
```
