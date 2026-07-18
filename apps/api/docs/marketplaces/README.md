# Marketplace Integration Foundation

Reusable multi-channel marketplace framework with **eBay** as the first adapter.

## What this module does

- Marketplace registry / factory / adapter interfaces  
- Async HTTP client with retries + rate-limit handling  
- API gateway pattern for channel REST APIs  
- eBay OAuth2 authorize + token exchange + refresh  
- Encrypted credential & token storage  
- Connection lifecycle (connect / callback / disconnect / validate / health)  
- Webhook receiver foundation  
- Monitoring logs (API calls, refresh history, sync history placeholders)  

## What it does **not** do

Listings, orders, inventory, messages, returns, pricing, AI, or business sync jobs.

## Docs

- [Architecture](ARCHITECTURE.md)  
- [eBay Integration](EBAY.md)  
- [OAuth](OAUTH.md)  
- [API Gateway](GATEWAY.md)  
- [Developer Guide](DEVELOPER.md)  
