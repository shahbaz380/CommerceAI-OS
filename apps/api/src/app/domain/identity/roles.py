"""System roles and default permission grants."""

from __future__ import annotations

from enum import StrEnum

from app.domain.identity.permissions import PermissionCode


class RoleCode(StrEnum):
    SUPER_ADMIN = "super_admin"
    ORGANIZATION_OWNER = "organization_owner"
    MANAGER = "manager"
    STAFF = "staff"
    SUPPORT = "support"
    READ_ONLY = "read_only"
    AI_AGENT = "ai_agent"
    MARKETPLACE_SERVICE = "marketplace_service"


SYSTEM_ROLES: dict[str, str] = {
    RoleCode.SUPER_ADMIN: "Platform Super Admin",
    RoleCode.ORGANIZATION_OWNER: "Organization Owner",
    RoleCode.MANAGER: "Manager",
    RoleCode.STAFF: "Staff / Operator",
    RoleCode.SUPPORT: "Support Agent",
    RoleCode.READ_ONLY: "Read Only",
    RoleCode.AI_AGENT: "Future AI Agent principal",
    RoleCode.MARKETPLACE_SERVICE: "Future marketplace service principal",
}


def role_permission_map() -> dict[str, list[str]]:
    """Default permission grants per system role."""
    all_perms = [p.value for p in PermissionCode]

    owner = [
        PermissionCode.IDENTITY_USER_READ,
        PermissionCode.IDENTITY_USER_WRITE,
        PermissionCode.IDENTITY_ROLE_READ,
        PermissionCode.IDENTITY_SESSION_REVOKE,
        PermissionCode.WORKSPACE_READ,
        PermissionCode.WORKSPACE_WRITE,
        PermissionCode.WORKSPACE_MEMBER_INVITE,
        PermissionCode.WORKSPACE_MEMBER_MANAGE,
        PermissionCode.WORKSPACE_BILLING,
        PermissionCode.PRODUCT_READ,
        PermissionCode.PRODUCT_WRITE,
        PermissionCode.PRODUCT_ARCHIVE,
        PermissionCode.PRODUCT_MANAGE_VARIANTS,
        PermissionCode.PRODUCT_MANAGE_MEDIA,
        PermissionCode.PRODUCT_MANAGE_CATEGORIES,
        PermissionCode.LISTING_READ,
        PermissionCode.LISTING_WRITE,
        PermissionCode.LISTING_VALIDATE,
        PermissionCode.LISTING_APPROVE,
        PermissionCode.LISTING_SCHEDULE,
        PermissionCode.LISTING_ARCHIVE,
        PermissionCode.LISTING_TEMPLATE_MANAGE,
        PermissionCode.LISTING_PUBLISH,
        PermissionCode.INVENTORY_READ,
        PermissionCode.INVENTORY_WRITE,
        PermissionCode.ORDER_READ,
        PermissionCode.ORDER_WRITE,
        PermissionCode.SUPPORT_READ,
        PermissionCode.SUPPORT_REPLY,
        PermissionCode.ANALYTICS_READ,
        PermissionCode.PRICING_READ,
        PermissionCode.PRICING_WRITE,
        PermissionCode.AI_USE,
        PermissionCode.AI_APPROVE,
        PermissionCode.MARKETPLACE_CONNECT,
        PermissionCode.MARKETPLACE_SYNC,
        PermissionCode.MARKETPLACE_CONNECTIONS_CREATE,
        PermissionCode.MARKETPLACE_CONNECTIONS_READ,
        PermissionCode.MARKETPLACE_CONNECTIONS_UPDATE,
        PermissionCode.MARKETPLACE_CONNECTIONS_DELETE,
        PermissionCode.MARKETPLACE_CONNECTIONS_REFRESH,
        PermissionCode.MARKETPLACE_CONNECTIONS_VALIDATE,
    ]

    manager = [
        PermissionCode.IDENTITY_USER_READ,
        PermissionCode.IDENTITY_ROLE_READ,
        PermissionCode.WORKSPACE_READ,
        PermissionCode.WORKSPACE_WRITE,
        PermissionCode.WORKSPACE_MEMBER_INVITE,
        PermissionCode.PRODUCT_READ,
        PermissionCode.PRODUCT_WRITE,
        PermissionCode.PRODUCT_ARCHIVE,
        PermissionCode.PRODUCT_MANAGE_VARIANTS,
        PermissionCode.PRODUCT_MANAGE_MEDIA,
        PermissionCode.PRODUCT_MANAGE_CATEGORIES,
        PermissionCode.LISTING_READ,
        PermissionCode.LISTING_WRITE,
        PermissionCode.LISTING_VALIDATE,
        PermissionCode.LISTING_APPROVE,
        PermissionCode.LISTING_SCHEDULE,
        PermissionCode.LISTING_ARCHIVE,
        PermissionCode.LISTING_TEMPLATE_MANAGE,
        PermissionCode.LISTING_PUBLISH,
        PermissionCode.INVENTORY_READ,
        PermissionCode.INVENTORY_WRITE,
        PermissionCode.ORDER_READ,
        PermissionCode.ORDER_WRITE,
        PermissionCode.SUPPORT_READ,
        PermissionCode.SUPPORT_REPLY,
        PermissionCode.ANALYTICS_READ,
        PermissionCode.PRICING_READ,
        PermissionCode.PRICING_WRITE,
        PermissionCode.AI_USE,
        PermissionCode.AI_APPROVE,
        PermissionCode.MARKETPLACE_SYNC,
        PermissionCode.MARKETPLACE_CONNECTIONS_CREATE,
        PermissionCode.MARKETPLACE_CONNECTIONS_READ,
        PermissionCode.MARKETPLACE_CONNECTIONS_UPDATE,
        PermissionCode.MARKETPLACE_CONNECTIONS_DELETE,
        PermissionCode.MARKETPLACE_CONNECTIONS_REFRESH,
        PermissionCode.MARKETPLACE_CONNECTIONS_VALIDATE,
    ]

    staff = [
        PermissionCode.WORKSPACE_READ,
        PermissionCode.PRODUCT_READ,
        PermissionCode.PRODUCT_WRITE,
        PermissionCode.PRODUCT_MANAGE_VARIANTS,
        PermissionCode.PRODUCT_MANAGE_MEDIA,
        PermissionCode.LISTING_READ,
        PermissionCode.LISTING_WRITE,
        PermissionCode.LISTING_VALIDATE,
        PermissionCode.INVENTORY_READ,
        PermissionCode.INVENTORY_WRITE,
        PermissionCode.ORDER_READ,
        PermissionCode.ORDER_WRITE,
        PermissionCode.SUPPORT_READ,
        PermissionCode.SUPPORT_REPLY,
        PermissionCode.AI_USE,
        PermissionCode.MARKETPLACE_CONNECTIONS_READ,
        PermissionCode.MARKETPLACE_CONNECTIONS_VALIDATE,
    ]

    support = [
        PermissionCode.WORKSPACE_READ,
        PermissionCode.ORDER_READ,
        PermissionCode.SUPPORT_READ,
        PermissionCode.SUPPORT_REPLY,
        PermissionCode.AI_USE,
    ]

    read_only = [
        PermissionCode.WORKSPACE_READ,
        PermissionCode.PRODUCT_READ,
        PermissionCode.LISTING_READ,
        PermissionCode.INVENTORY_READ,
        PermissionCode.ORDER_READ,
        PermissionCode.SUPPORT_READ,
        PermissionCode.ANALYTICS_READ,
        PermissionCode.PRICING_READ,
        PermissionCode.AI_USE,
        PermissionCode.MARKETPLACE_CONNECTIONS_READ,
    ]

    ai_agent = [
        PermissionCode.AI_USE,
        PermissionCode.PRODUCT_READ,
        PermissionCode.LISTING_READ,
        PermissionCode.INVENTORY_READ,
        PermissionCode.ORDER_READ,
        PermissionCode.ANALYTICS_READ,
    ]

    marketplace_svc = [
        PermissionCode.MARKETPLACE_SYNC,
        PermissionCode.PRODUCT_READ,
        PermissionCode.LISTING_READ,
        PermissionCode.LISTING_WRITE,
        PermissionCode.ORDER_READ,
        PermissionCode.INVENTORY_READ,
        PermissionCode.INVENTORY_WRITE,
    ]

    return {
        RoleCode.SUPER_ADMIN: all_perms,
        RoleCode.ORGANIZATION_OWNER: [p.value for p in owner],
        RoleCode.MANAGER: [p.value for p in manager],
        RoleCode.STAFF: [p.value for p in staff],
        RoleCode.SUPPORT: [p.value for p in support],
        RoleCode.READ_ONLY: [p.value for p in read_only],
        RoleCode.AI_AGENT: [p.value for p in ai_agent],
        RoleCode.MARKETPLACE_SERVICE: [p.value for p in marketplace_svc],
    }
