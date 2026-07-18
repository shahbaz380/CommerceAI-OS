"""Marketplace domain enumerations."""

from __future__ import annotations

from enum import StrEnum


class MarketplaceChannel(StrEnum):
    EBAY = "ebay"
    AMAZON = "amazon"
    SHOPIFY = "shopify"
    WALMART = "walmart"
    WOOCOMMERCE = "woocommerce"
    TIKTOK = "tiktok"
    FACEBOOK = "facebook"


class MarketplaceEnvironment(StrEnum):
    SANDBOX = "sandbox"
    PRODUCTION = "production"


class ConnectionStatus(StrEnum):
    PENDING = "pending"
    CONNECTED = "connected"
    REAUTH_REQUIRED = "reauth_required"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    SUSPENDED = "suspended"


class SyncJobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MarketplaceLogLevel(StrEnum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
