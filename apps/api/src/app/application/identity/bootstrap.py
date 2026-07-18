"""Seed system roles and permissions."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.identity.permissions import SYSTEM_PERMISSIONS
from app.domain.identity.roles import SYSTEM_ROLES, role_permission_map
from app.infrastructure.logging.setup import get_logger
from app.infrastructure.persistence.models.identity import (
    PermissionModel,
    RoleModel,
    RolePermissionModel,
)
from app.infrastructure.persistence.repositories.identity import PermissionRepository, RoleRepository

logger = get_logger("app.security")

_ROLE_RANK = {
    "super_admin": 0,
    "organization_owner": 10,
    "manager": 20,
    "staff": 30,
    "support": 40,
    "read_only": 50,
    "ai_agent": 60,
    "marketplace_service": 70,
}


async def seed_identity_catalog(session: AsyncSession) -> dict[str, int]:
    """Idempotently ensure system roles/permissions exist (async-safe, no lazy IO)."""
    role_repo = RoleRepository(session)
    perm_repo = PermissionRepository(session)

    perm_by_code: dict[str, PermissionModel] = {}
    created_perms = 0
    for code, (module, description) in SYSTEM_PERMISSIONS.items():
        existing = await perm_repo.get_by_code(code)
        if existing:
            perm_by_code[code] = existing
            continue
        perm = PermissionModel(code=code, module=module, description=description, is_system=True)
        await perm_repo.add(perm)
        perm_by_code[code] = perm
        created_perms += 1

    grants = role_permission_map()
    created_roles = 0
    for code, name in SYSTEM_ROLES.items():
        role = await role_repo.get_by_code(code)
        if role is None:
            role = RoleModel(
                code=code,
                name=name,
                description=name,
                is_system=True,
                hierarchy_rank=_ROLE_RANK.get(code, 100),
            )
            await role_repo.add(role)
            created_roles += 1
            existing_perm_ids: set = set()
        else:
            # explicit query for linked permission ids (no lazy load)
            stmt = (
                select(RolePermissionModel.permission_id)
                .where(RolePermissionModel.role_id == role.id)
            )
            result = await session.execute(stmt)
            existing_perm_ids = set(result.scalars().all())

        for pcode in grants.get(code, []):
            perm = perm_by_code.get(pcode)
            if perm is None:
                continue
            if perm.id in existing_perm_ids:
                continue
            session.add(RolePermissionModel(role_id=role.id, permission_id=perm.id))
            existing_perm_ids.add(perm.id)

    await session.flush()
    logger.info("identity_catalog_seeded", roles=created_roles, permissions=created_perms)
    return {"roles_created": created_roles, "permissions_created": created_perms}
