"""Marketplace OAuth / connection domain exceptions."""

from __future__ import annotations

from app.shared.exceptions import AppError, AuthorizationError, BusinessRuleError, ConflictError, NotFoundError


class OAuthStateInvalid(BusinessRuleError):
    def __init__(self, message: str = "Invalid OAuth state") -> None:
        super().__init__(message, code="OAUTH_STATE_INVALID")


class OAuthStateExpired(BusinessRuleError):
    def __init__(self, message: str = "OAuth state expired") -> None:
        super().__init__(message, code="OAUTH_STATE_EXPIRED")


class OAuthReplayAttack(BusinessRuleError):
    def __init__(self, message: str = "OAuth state already used (possible replay)") -> None:
        super().__init__(message, code="OAUTH_REPLAY_ATTACK")


class AuthorizationFailed(AppError):
    code = "AUTHORIZATION_FAILED"
    http_status = 400

    def __init__(self, message: str = "Marketplace authorization failed") -> None:
        super().__init__(message, code=self.code, retryable=False)


class TokenExchangeFailed(AppError):
    code = "TOKEN_EXCHANGE_FAILED"
    http_status = 502

    def __init__(self, message: str = "Token exchange failed", *, cause: Exception | None = None) -> None:
        super().__init__(message, code=self.code, retryable=True, cause=cause)


class TokenRefreshFailed(AppError):
    code = "TOKEN_REFRESH_FAILED"
    http_status = 502

    def __init__(self, message: str = "Token refresh failed", *, cause: Exception | None = None) -> None:
        super().__init__(message, code=self.code, retryable=True, cause=cause)


class MarketplaceDisconnected(BusinessRuleError):
    def __init__(self, message: str = "Marketplace connection is disconnected") -> None:
        super().__init__(message, code="MARKETPLACE_DISCONNECTED")


class MarketplaceAlreadyConnected(ConflictError):
    def __init__(self, message: str = "Marketplace account already connected") -> None:
        super().__init__(message, code="MARKETPLACE_ALREADY_CONNECTED")


class InvalidMarketplaceConnection(NotFoundError):
    def __init__(self, message: str = "Invalid marketplace connection") -> None:
        super().__init__(message, code="INVALID_MARKETPLACE_CONNECTION")


class MarketplacePermissionDenied(AuthorizationError):
    def __init__(self, message: str = "Marketplace permission denied") -> None:
        super().__init__(message, code="MARKETPLACE_PERMISSION_DENIED")


class MarketplaceRefreshInProgress(ConflictError):
    def __init__(self, message: str = "Token refresh already in progress") -> None:
        super().__init__(message, code="MARKETPLACE_REFRESH_IN_PROGRESS")
