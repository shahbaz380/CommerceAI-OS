# eBay OAuth Account Connection Guide (Prompt 18)

## User journey

1. Store developer credentials for workspace (`client_id`, `client_secret`, `redirect_uri` / RuName).  
2. `GET /api/v1/marketplaces/ebay/workspaces/{workspace_id}/connect`  
3. Redirect browser to `authorization_url`.  
4. eBay redirects back with `code` + `state`.  
5. `POST /api/v1/marketplaces/ebay/workspaces/{workspace_id}/callback`  
6. Connection becomes `connected`; tokens encrypted at rest.

## Multi-account

- Multiple eBay accounts per workspace  
- First connected account becomes `is_default`  
- `PATCH .../accounts/{id}/default` to change default  
- `alias` for human labels  

## Token lifecycle

- Access token stored encrypted; refresh token encrypted  
- Refresh rotates token rows (`is_current`)  
- Concurrent refresh blocked via Redis lock (fail-open if Redis down)  
- Missing/failed refresh → `reauth_required`  
- Disconnect best-effort revokes refresh token at eBay then clears local tokens  

## Environments

- `sandbox` and `production` credentials are separate  
- Connection records store environment  

## Security

- Single-use state (DB + Redis)  
- State bound to workspace, channel, user, connection  
- 15-minute expiry  
- Replay detection  
- Secrets never returned by APIs  
