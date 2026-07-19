"""RBAC engine tests."""

import uuid

import pytest

from app.application.identity.authorization import AuthorizationService, Principal
from app.shared.exceptions import AuthorizationError


def test_permission_granted() -> None:
    p = Principal(
        user_id=uuid.uuid4(),
        email="a@b.com",
        permissions=["listing.read"],
    )
    authz = AuthorizationService()
    assert authz.require_permission(p, "listing.read") is p


def test_permission_denied() -> None:
    p = Principal(user_id=uuid.uuid4(), email="a@b.com", permissions=[])
    authz = AuthorizationService()
    with pytest.raises(AuthorizationError):
        authz.require_permission(p, "listing.write")


def test_superuser_bypasses() -> None:
    p = Principal(user_id=uuid.uuid4(), email="a@b.com", is_superuser=True)
    authz = AuthorizationService()
    authz.require_permission(p, "platform.admin")
