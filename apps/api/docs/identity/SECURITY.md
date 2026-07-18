# Identity Security Guide

## Password storage

- **Argon2** via passlib  
- Strength policy: length ≥ 12, upper, lower, digit, special  

## Tokens

- JWT signed with `SECRET_KEY` (HS256 default)  
- Refresh tokens stored as **SHA-256 hashes** only  
- Refresh reuse / hash mismatch revokes all user refresh tokens  

## Transport / headers

Existing middleware:

- Security headers (nosniff, frame deny, …)  
- CORS allowlist  
- Request/correlation IDs  

CSRF: Bearer-token SPA pattern (no cookie session auth by default). If cookie auth is added later, enable CSRF tokens.

## Rate limiting

`RATE_LIMIT_ENABLED` middleware placeholder — wire Redis limiter before production abuse exposure.

## OAuth

Provider registry supports ebay/google/microsoft/github/amazon/shopify **placeholders only**.
