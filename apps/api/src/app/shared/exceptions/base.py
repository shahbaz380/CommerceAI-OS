"""Application exception hierarchy — maps cleanly to HTTP problem details."""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Base application error."""

    code: str = "APP_ERROR"
    http_status: int = 500
    retryable: bool = False

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        details: list[dict[str, Any]] | None = None,
        retryable: bool | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        self.details = details or []
        if retryable is not None:
            self.retryable = retryable
        self.cause = cause

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
            "retryable": self.retryable,
        }


class ValidationAppError(AppError):
    code = "VALIDATION_ERROR"
    http_status = 400

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        details: list[dict[str, Any]] | None = None,
        retryable: bool | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(
            message,
            code=code,
            details=details,
            retryable=retryable,
            cause=cause,
        )


class AuthenticationError(AppError):
    code = "AUTHENTICATION_ERROR"
    http_status = 401


class AuthorizationError(AppError):
    code = "AUTHORIZATION_ERROR"
    http_status = 403


class NotFoundError(AppError):
    code = "NOT_FOUND"
    http_status = 404


class ConflictError(AppError):
    code = "CONFLICT"
    http_status = 409


class BusinessRuleError(AppError):
    code = "BUSINESS_RULE_VIOLATION"
    http_status = 422


class RateLimitError(AppError):
    code = "RATE_LIMIT_EXCEEDED"
    http_status = 429
    retryable = True


class DependencyError(AppError):
    code = "DEPENDENCY_ERROR"
    http_status = 503
    retryable = True


class AIError(AppError):
    """AI plane errors (provider, safety, budget)."""

    code = "AI_ERROR"
    http_status = 502
    retryable = True


class MarketplaceError(AppError):
    """Marketplace adapter errors (eBay, etc.)."""

    code = "MARKETPLACE_ERROR"
    http_status = 502
    retryable = True

    def __init__(
        self,
        message: str,
        *,
        provider: str | None = None,
        provider_code: str | None = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", None) or []
        if provider:
            details.append({"field": "provider", "issue": provider})
        if provider_code:
            details.append({"field": "providerCode", "issue": provider_code})
        super().__init__(message, details=details, **kwargs)
        self.provider = provider
        self.provider_code = provider_code
