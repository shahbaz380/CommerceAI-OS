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

    # Catalog
    PRODUCT_READ = "product.read"
    PRODUCT_WRITE = "product.write"
    PRODUCT_ARCHIVE = "product.archive"
    PRODUCT_MANAGE_VARIANTS = "product.manage_variants"
    PRODUCT_MANAGE_MEDIA = "product.manage_media"
    PRODUCT_MANAGE_CATEGORIES = "product.manage_categories"

    # Listings
    LISTING_READ = "listing.read"
    LISTING_WRITE = "listing.write"
    LISTING_VALIDATE = "listing.validate"
    LISTING_APPROVE = "listing.approve"
    LISTING_SCHEDULE = "listing.schedule"
    LISTING_ARCHIVE = "listing.archive"
    LISTING_TEMPLATE_MANAGE = "listing_template.manage"
    LISTING_PUBLISH = "listing.publish"

    # Future commerce
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
    MARKETPLACE_CONNECTIONS_CREATE = "marketplace_connections:create"
    MARKETPLACE_CONNECTIONS_READ = "marketplace_connections:read"
    MARKETPLACE_CONNECTIONS_UPDATE = "marketplace_connections:update"
    MARKETPLACE_CONNECTIONS_DELETE = "marketplace_connections:delete"
    MARKETPLACE_CONNECTIONS_REFRESH = "marketplace_connections:refresh"
    MARKETPLACE_CONNECTIONS_VALIDATE = "marketplace_connections:validate"


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
    PermissionCode.PRODUCT_READ: ("product", "View products"),
    PermissionCode.PRODUCT_WRITE: ("product", "Create/update products"),
    PermissionCode.PRODUCT_ARCHIVE: ("product", "Archive products"),
    PermissionCode.PRODUCT_MANAGE_VARIANTS: ("product", "Manage product variants"),
    PermissionCode.PRODUCT_MANAGE_MEDIA: ("product", "Manage product media"),
    PermissionCode.PRODUCT_MANAGE_CATEGORIES: ("product", "Manage product categories"),
    PermissionCode.LISTING_READ: ("listing", "View listings"),
    PermissionCode.LISTING_WRITE: ("listing", "Edit listings"),
    PermissionCode.LISTING_VALIDATE: ("listing", "Validate listings"),
    PermissionCode.LISTING_APPROVE: ("listing", "Approve listings"),
    PermissionCode.LISTING_SCHEDULE: ("listing", "Schedule listings"),
    PermissionCode.LISTING_ARCHIVE: ("listing", "Archive listings"),
    PermissionCode.LISTING_TEMPLATE_MANAGE: ("listing", "Manage listing templates"),
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
    PermissionCode.MARKETPLACE_CONNECTIONS_CREATE: ("marketplace", "Create marketplace connections"),
    PermissionCode.MARKETPLACE_CONNECTIONS_READ: ("marketplace", "Read marketplace connections"),
    PermissionCode.MARKETPLACE_CONNECTIONS_UPDATE: ("marketplace", "Update marketplace connections"),
    PermissionCode.MARKETPLACE_CONNECTIONS_DELETE: ("marketplace", "Delete marketplace connections"),
    PermissionCode.MARKETPLACE_CONNECTIONS_REFRESH: ("marketplace", "Refresh marketplace tokens"),
    PermissionCode.MARKETPLACE_CONNECTIONS_VALIDATE: ("marketplace", "Validate marketplace connections"),
}
