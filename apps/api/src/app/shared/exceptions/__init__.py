"""Shared exception taxonomy."""

from app.shared.exceptions.base import (
    AIError,
    AppError,
    AuthenticationError,
    AuthorizationError,
    BusinessRuleError,
    ConflictError,
    DependencyError,
    MarketplaceError,
    NotFoundError,
    RateLimitError,
    ValidationAppError,
)

__all__ = [
    "AIError",
    "AppError",
    "AuthenticationError",
    "AuthorizationError",
    "BusinessRuleError",
    "ConflictError",
    "DependencyError",
    "MarketplaceError",
    "NotFoundError",
    "RateLimitError",
    "ValidationAppError",
]
