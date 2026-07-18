"""Unit tests for tenancy domain helpers."""

from app.domain.tenancy.enums import WorkspaceRole, role_at_least


def test_role_hierarchy() -> None:
    assert role_at_least(WorkspaceRole.OWNER, WorkspaceRole.MANAGER)
    assert role_at_least(WorkspaceRole.MANAGER, WorkspaceRole.STAFF)
    assert not role_at_least(WorkspaceRole.STAFF, WorkspaceRole.MANAGER)
