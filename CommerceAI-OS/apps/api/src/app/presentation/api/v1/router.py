"""Aggregate API v1 router."""

from __future__ import annotations

from fastapi import APIRouter

from app.presentation.api.v1.routes import (
    auth,
    health,
    identity,
    marketplaces,
    organizations,
    profiles,
    workspaces,
)

api_v1_router = APIRouter()
api_v1_router.include_router(health.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(identity.router)
api_v1_router.include_router(organizations.router)
api_v1_router.include_router(workspaces.router)
api_v1_router.include_router(profiles.router)
api_v1_router.include_router(marketplaces.router)
