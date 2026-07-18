"""System permission catalog (RBAC)."""

from __future__ import annotations

from enum import StrEnum


class PermissionCode(StrEnum):
    # Platform
    PLATFORM_ADMIN = "platform.admin"
    PLATFORM_AUDIT_READ = "platform.audit.read"

    # Identity
    IDENTITY_USER_READ = "identity.user.read"
    IDENTITY_USER_WRITE = "identity.user.write"
    IDENTITY_ROLE_READ = "identity.role.read"
    IDENTITY_ROLE_WRITE = "identity.role.write"
    IDENTITY_SESSION_REVOKE = "identity.session.revoke"

    # Workspace (foundation for Prompt 15)
    WORKSPACE_READ = "workspace.read"
    WORKSPACE_WRITE = "workspace.write"
    WORKSPACE_MEMBER_INVITE = "workspace.member.invite"
    WORKSPACE_MEMBER_MANAGE = "workspace.member.manage"
    WORKSPACE_BILLING = "workspace.billing"

    # Future commerce (seeded codes — not enforced by business modules yet)
    LISTING_READ = "listing.read"
    LISTING_WRITE = "listing.write"
    LISTING_PUBLISH = "listing.publish"
    INVENTORY_READ = "inventory.read"
    INVENTORY_WRITE = "inventory.write"
    ORDER_READ = "order.read"
    ORDER_WRITE = "order.write"
    SUPPORT_READ = "support.read"
    SUPPORT_REPLY = "support.reply"
    ANALYTICS_READ = "analytics.read"
    PRICING_READ = "pricing.read"
    PRICING_WRITE = "pricing.write"
    AI_USE = "ai.use"
    AI_APPROVE = "ai.approve"
    MARKETPLACE_CONNECT = "marketplace.connect"
    MARKETPLACE_SYNC = "marketplace.sync"


# code -> (module, description)
SYSTEM_PERMISSIONS: dict[str, tuple[str, str]] = {
    PermissionCode.PLATFORM_ADMIN: ("platform", "Full platform administration"),
    PermissionCode.PLATFORM_AUDIT_READ: ("platform", "Read platform audit logs"),
    PermissionCode.IDENTITY_USER_READ: ("identity", "View users"),
    PermissionCode.IDENTITY_USER_WRITE: ("identity", "Manage users"),
    PermissionCode.IDENTITY_ROLE_READ: ("identity", "View roles"),
    PermissionCode.IDENTITY_ROLE_WRITE: ("identity", "Manage roles"),
    PermissionCode.IDENTITY_SESSION_REVOKE: ("identity", "Revoke sessions"),
    PermissionCode.WORKSPACE_READ: ("workspace", "View workspace"),
    PermissionCode.WORKSPACE_WRITE: ("workspace", "Edit workspace settings"),
    PermissionCode.WORKSPACE_MEMBER_INVITE: ("workspace", "Invite members"),
    PermissionCode.WORKSPACE_MEMBER_MANAGE: ("workspace", "Manage members"),
    PermissionCode.WORKSPACE_BILLING: ("workspace", "Manage billing"),
    PermissionCode.LISTING_READ: ("listing", "View listings"),
    PermissionCode.LISTING_WRITE: ("listing", "Edit listings"),
    PermissionCode.LISTING_PUBLISH: ("listing", "Publish listings"),
    PermissionCode.INVENTORY_READ: ("inventory", "View inventory"),
    PermissionCode.INVENTORY_WRITE: ("inventory", "Edit inventory"),
    PermissionCode.ORDER_READ: ("order", "View orders"),
    PermissionCode.ORDER_WRITE: ("order", "Manage orders"),
    PermissionCode.SUPPORT_READ: ("support", "View support inbox"),
    PermissionCode.SUPPORT_REPLY: ("support", "Reply to buyers"),
    PermissionCode.ANALYTICS_READ: ("analytics", "View analytics"),
    PermissionCode.PRICING_READ: ("pricing", "View pricing"),
    PermissionCode.PRICING_WRITE: ("pricing", "Change pricing"),
    PermissionCode.AI_USE: ("ai", "Use AI assistant"),
    PermissionCode.AI_APPROVE: ("ai", "Approve AI actions"),
    PermissionCode.MARKETPLACE_CONNECT: ("marketplace", "Connect channels"),
    PermissionCode.MARKETPLACE_SYNC: ("marketplace", "Trigger sync"),
}
