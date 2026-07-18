"""Identity-specific repositories."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.persistence.models.identity import (
    LoginHistoryModel,
    PermissionModel,
    RefreshTokenModel,
    RoleModel,
    RolePermissionModel,
    SecurityEventModel,
    UserModel,
    UserRoleModel,
    UserSessionModel,
)


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: uuid.UUID) -> UserModel | None:
        stmt = (
            select(UserModel)
            .where(UserModel.id == user_id, UserModel.deleted_at.is_(None))
            .options(selectinload(UserModel.roles).selectinload(UserRoleModel.role))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> UserModel | None:
        stmt = (
            select(UserModel)
            .where(UserModel.email == email.lower(), UserModel.deleted_at.is_(None))
            .options(selectinload(UserModel.roles).selectinload(UserRoleModel.role))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> UserModel | None:
        stmt = select(UserModel).where(
            UserModel.username == username,
            UserModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add(self, user: UserModel) -> UserModel:
        self.session.add(user)
        await self.session.flush()
        return user


class RoleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_code(self, code: str) -> RoleModel | None:
        stmt = (
            select(RoleModel)
            .where(RoleModel.code == code, RoleModel.deleted_at.is_(None))
            .options(selectinload(RoleModel.permissions).selectinload(RolePermissionModel.permission))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self) -> list[RoleModel]:
        stmt = select(RoleModel).where(RoleModel.deleted_at.is_(None)).order_by(RoleModel.hierarchy_rank)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add(self, role: RoleModel) -> RoleModel:
        self.session.add(role)
        await self.session.flush()
        return role


class PermissionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_code(self, code: str) -> PermissionModel | None:
        stmt = select(PermissionModel).where(
            PermissionModel.code == code,
            PermissionModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self) -> list[PermissionModel]:
        stmt = select(PermissionModel).where(PermissionModel.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add(self, permission: PermissionModel) -> PermissionModel:
        self.session.add(permission)
        await self.session.flush()
        return permission


class SessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, model: UserSessionModel) -> UserSessionModel:
        self.session.add(model)
        await self.session.flush()
        return model

    async def get_by_token_hash(self, token_hash: str) -> UserSessionModel | None:
        stmt = select(UserSessionModel).where(UserSessionModel.session_token_hash == token_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, session_id: uuid.UUID) -> UserSessionModel | None:
        stmt = select(UserSessionModel).where(UserSessionModel.id == session_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_active_for_user(self, user_id: uuid.UUID) -> list[UserSessionModel]:
        now = datetime.now(UTC)
        stmt = select(UserSessionModel).where(
            UserSessionModel.user_id == user_id,
            UserSessionModel.revoked_at.is_(None),
        )
        result = await self.session.execute(stmt)
        sessions = list(result.scalars().all())
        active: list[UserSessionModel] = []
        for s in sessions:
            exp = s.expires_at
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=UTC)
            if exp > now:
                active.append(s)
        return active

    async def revoke(self, model: UserSessionModel) -> None:
        model.revoked_at = datetime.now(UTC)
        await self.session.flush()

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> int:
        sessions = await self.list_active_for_user(user_id)
        for s in sessions:
            s.revoked_at = datetime.now(UTC)
        await self.session.flush()
        return len(sessions)


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, model: RefreshTokenModel) -> RefreshTokenModel:
        self.session.add(model)
        await self.session.flush()
        return model

    async def get_by_jti(self, jti: str) -> RefreshTokenModel | None:
        stmt = select(RefreshTokenModel).where(RefreshTokenModel.jti == jti)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke(self, model: RefreshTokenModel, *, replaced_by: str | None = None) -> None:
        model.revoked_at = datetime.now(UTC)
        if replaced_by:
            model.replaced_by_jti = replaced_by
        await self.session.flush()

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        stmt = select(RefreshTokenModel).where(
            RefreshTokenModel.user_id == user_id,
            RefreshTokenModel.revoked_at.is_(None),
        )
        result = await self.session.execute(stmt)
        for token in result.scalars().all():
            token.revoked_at = datetime.now(UTC)
        await self.session.flush()


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_login(self, row: LoginHistoryModel) -> None:
        self.session.add(row)
        await self.session.flush()

    async def add_security_event(self, row: SecurityEventModel) -> None:
        self.session.add(row)
        await self.session.flush()
