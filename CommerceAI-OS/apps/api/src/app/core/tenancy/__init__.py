"""Multi-tenant helpers (no auth yet)."""

from app.core.tenancy.context import resolve_tenant_from_headers

__all__ = ["resolve_tenant_from_headers"]
