# Connection Management

| Action | Endpoint |
|--------|----------|
| Connect | `GET /marketplaces/ebay/workspaces/{ws}/connect` |
| Callback | `POST /marketplaces/ebay/workspaces/{ws}/callback` |
| List | `GET /marketplaces/ebay/workspaces/{ws}/accounts` |
| Status | `GET /marketplaces/ebay/workspaces/{ws}/status` |
| Refresh | `POST .../accounts/{id}/refresh` |
| Validate | `POST .../accounts/{id}/validate` |
| Health | `GET .../accounts/{id}/health` |
| Disconnect | `POST .../accounts/{id}/disconnect` |
| Reconnect | `POST .../accounts/{id}/reconnect` |
| Default | `PATCH .../accounts/{id}/default` |
| Suspend/Resume | `POST .../suspend` · `POST .../resume` |
| Remove | `DELETE .../accounts/{id}` |

Statuses: `pending`, `connected`, `reauth_required`, `disconnected`, `error`, `suspended`, `deactivated`
