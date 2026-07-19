"""User profile service."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.identity.authorization import Principal
from app.infrastructure.persistence.models.tenancy import UserProfileModel
from app.infrastructure.persistence.repositories.tenancy import ProfileRepository, TenantAuditRepository
from app.shared.exceptions import AuthorizationError


class ProfileService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.profiles = ProfileRepository(session)
        self.audit = TenantAuditRepository(session)

    async def get_or_create(self, user_id: uuid.UUID) -> UserProfileModel:
        profile = await self.profiles.get_by_user_id(user_id)
        if profile is None:
            profile = await self.profiles.add(
                UserProfileModel(
                    user_id=user_id,
                    notification_preferences={"email": True, "in_app": True},
                    ui_preferences={"density": "comfortable"},
                )
            )
        return profile

    async def get_mine(self, principal: Principal) -> UserProfileModel:
        return await self.get_or_create(principal.user_id)

    async def update_mine(
        self,
        principal: Principal,
        **fields,
    ) -> UserProfileModel:
        profile = await self.get_or_create(principal.user_id)
        for key in (
            "display_name",
            "avatar_url",
            "phone",
            "job_title",
            "bio",
            "timezone",
            "language",
            "theme",
            "notification_preferences",
            "ui_preferences",
        ):
            if key in fields and fields[key] is not None:
                setattr(profile, key, fields[key])
        await self.audit.add(
            event_type="profile.updated",
            message="User profile updated",
            actor_user_id=principal.user_id,
            metadata={"user_id": str(principal.user_id)},
        )
        await self.session.flush()
        return profile

    async def get_user_profile(self, principal: Principal, user_id: uuid.UUID) -> UserProfileModel:
        # self or superuser for now; workspace peer visibility can expand later
        if principal.user_id != user_id and not principal.is_superuser:
            raise AuthorizationError("Cannot view this profile", code="PROFILE_ACCESS_DENIED")
        return await self.get_or_create(user_id)
