"""Tenancy enumerations."""

from __future__ import annotations

from enum import StrEnum


class OrganizationStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"
    ARCHIVED = "archived"


class WorkspaceStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class MembershipStatus(StrEnum):
    ACTIVE = "active"
    INVITED = "invited"
    SUSPENDED = "suspended"
    REMOVED = "removed"


class InvitationStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REVOKED = "revoked"


class WorkspaceRole(StrEnum):
    """Workspace-scoped role codes (map to IAM RoleCode where applicable)."""

    OWNER = "organization_owner"
    MANAGER = "manager"
    STAFF = "staff"
    SUPPORT = "support"
    READ_ONLY = "read_only"


# Role hierarchy for workspace (lower = more privileged)
WORKSPACE_ROLE_RANK: dict[str, int] = {
    WorkspaceRole.OWNER: 10,
    WorkspaceRole.MANAGER: 20,
    WorkspaceRole.STAFF: 30,
    WorkspaceRole.SUPPORT: 40,
    WorkspaceRole.READ_ONLY: 50,
}


def role_at_least(member_role: str, required: str) -> bool:
    return WORKSPACE_ROLE_RANK.get(member_role, 999) <= WORKSPACE_ROLE_RANK.get(required, 0)
