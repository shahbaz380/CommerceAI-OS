# Token Lifecycle

```text
authorize → code exchange → store encrypted access+refresh
                │
                ▼
        access near expiry?
           /         \
         yes          no
          │            │
     refresh lock    use access
          │
   refresh endpoint
      /        \
  success     failure
    │            │
 rotate token  reauth_required
```

## Monitoring signals

- `marketplace_token_refresh_history.success`  
- connection `last_refreshed_at` / `last_validated_at`  
- `marketplace_api_logs` for identity probes  
- tenant audit: `marketplace.oauth.*`  
