"""Marketplace domain event names (for EventBus)."""

from __future__ import annotations

MARKETPLACE_CONNECTION_STARTED = "marketplace.connection.started"
MARKETPLACE_CONNECTION_CONNECTED = "marketplace.connection.connected"
MARKETPLACE_CONNECTION_DISCONNECTED = "marketplace.connection.disconnected"
MARKETPLACE_CONNECTION_REAUTH_REQUIRED = "marketplace.connection.reauth_required"
MARKETPLACE_TOKEN_REFRESHED = "marketplace.token.refreshed"
MARKETPLACE_TOKEN_REFRESH_FAILED = "marketplace.token.refresh_failed"
MARKETPLACE_API_ERROR = "marketplace.api.error"
MARKETPLACE_RATE_LIMITED = "marketplace.api.rate_limited"
MARKETPLACE_WEBHOOK_RECEIVED = "marketplace.webhook.received"
