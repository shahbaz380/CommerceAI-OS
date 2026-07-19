"""User profile API."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.application.identity.authorization import Principal
from app.application.tenancy.profile_service import ProfileService
from app.presentation.api.deps.auth import get_current_principal
from app.presentation.api.deps.tenancy import get_profile_service
from app.presentation.schemas.tenancy.schemas import ProfileResponse, ProfileUpdate

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ProfileService, Depends(get_profile_service)],
) -> ProfileResponse:
    p = await svc.get_mine(principal)
    return ProfileResponse.model_validate(p)


@router.patch("/me", response_model=ProfileResponse)
async def update_my_profile(
    body: ProfileUpdate,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ProfileService, Depends(get_profile_service)],
) -> ProfileResponse:
    p = await svc.update_mine(principal, **body.model_dump(exclude_unset=True))
    return ProfileResponse.model_validate(p)


@router.get("/{user_id}", response_model=ProfileResponse)
async def get_profile(
    user_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ProfileService, Depends(get_profile_service)],
) -> ProfileResponse:
    p = await svc.get_user_profile(principal, user_id)
    return ProfileResponse.model_validate(p)
