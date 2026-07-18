# eBay Integration Guide

## Environments

| Env | Auth | API |
|-----|------|-----|
| sandbox | `auth.sandbox.ebay.com` | `api.sandbox.ebay.com` |
| production | `auth.ebay.com` | `api.ebay.com` |

## Setup

1. Create eBay developer application.  
2. Configure RuName / redirect URI.  
3. `POST /api/v1/marketplaces/workspaces/{id}/credentials` with client id/secret.  
4. `POST .../connect` → open `authorization_url`.  
5. `POST .../connect/callback` with `code` + `state`.  

## Token storage

Access/refresh tokens encrypted at rest via `EncryptedString` (Fernet derived from `SECRET_KEY`).

## Status values

`pending` → `connected` → `reauth_required` / `disconnected` / `error`
