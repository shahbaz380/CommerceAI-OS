"""Webhook foundation — receive, verify placeholder, store, dispatch event."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events.bus import DomainEvent, get_event_bus
from app.domain.marketplaces.events import MARKETPLACE_WEBHOOK_RECEIVED
from app.infrastructure.logging.setup import get_logger
from app.infrastructure.persistence.models.marketplace import MarketplaceWebhookEventModel
from app.infrastructure.persistence.repositories.marketplace import MarketplaceLogRepository

logger = get_logger("app.marketplace")


class WebhookReceiver:
    """Architecture for inbound marketplace webhooks (no business handlers)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.logs = MarketplaceLogRepository(session)
        self.events = get_event_bus()

    def verify_signature(
        self,
        channel: str,
        *,
        headers: dict[str, str],
        body: bytes,
        secret: str | None,
    ) -> bool | None:
        """Return True/False if verified, None if verification not configured."""
        if not secret:
            return None
        # Channel-specific verification plugged in later (eBay notification signature, etc.)
        # Foundation: require presence of a signature header when secret configured.
        sig = headers.get("x-ebay-signature") or headers.get("x-marketplace-signature")
        if not sig:
            return False
        # Placeholder: accept non-empty signature when secret set (replace with real crypto)
        return len(sig) > 0

    async def receive(
        self,
        *,
        channel: str,
        headers: dict[str, str],
        payload: dict[str, Any] | None,
        event_type: str | None = None,
        secret: str | None = None,
        raw_body: bytes = b"",
    ) -> MarketplaceWebhookEventModel:
        valid = self.verify_signature(channel, headers=headers, body=raw_body, secret=secret)
        row = await self.logs.add_webhook(
            MarketplaceWebhookEventModel(
                channel=channel,
                event_type=event_type or (payload or {}).get("metadata", {}).get("topic"),
                signature_valid=valid,
                headers_json={k: v for k, v in headers.items() if k.lower() not in {"authorization"}},
                payload_json=payload,
                processed=False,
            )
        )
        await self.events.publish(
            DomainEvent(
                name=MARKETPLACE_WEBHOOK_RECEIVED,
                payload={
                    "webhook_id": str(row.id),
                    "channel": channel,
                    "event_type": row.event_type,
                    "signature_valid": valid,
                },
            )
        )
        logger.info(
            "marketplace_webhook_received",
            channel=channel,
            webhook_id=str(row.id),
            signature_valid=valid,
        )
        return row
