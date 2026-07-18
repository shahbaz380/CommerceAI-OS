# API Gateway Guide

## AsyncHttpClient

- Timeouts  
- Exponential backoff + jitter  
- Honors `Retry-After`  
- Retries 408/425/429/5xx  
- Raises `RateLimitError` / `DependencyError`  

## MarketplaceGateway

Channel gateways wrap base URL + bearer auth + JSON parsing.

`EbayApiGateway` provides foundation identity probe only — **no listings/orders methods**.
