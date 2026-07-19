"""Listing management API routes."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.identity.authorization import Principal
from app.application.listings.listing_service import ListingService
from app.presentation.api.deps.auth import get_current_principal
from app.presentation.api.deps.common import get_db_session
from app.presentation.schemas.identity.auth import MessageResponse
from app.presentation.schemas.listings.schemas import (
    ListingCreate,
    ListingListResponse,
    ListingPreviewResponse,
    ListingResponse,
    ListingScheduleRequest,
    ListingTemplateCreate,
    ListingTemplateResponse,
    ListingTemplateUpdate,
    ListingUpdate,
    ListingValidationIssueResponse,
    ListingValidationResponse,
    ListingVersionResponse,
)
from app.shared.exceptions import ValidationAppError

router = APIRouter(tags=["listings"])


def _require_workspace(x_workspace_id: str | None) -> UUID:
    if not x_workspace_id:
        raise ValidationAppError(
            "X-Workspace-Id header is required",
            details=[{"field": "X-Workspace-Id", "issue": "required"}],
        )
    try:
        return UUID(x_workspace_id)
    except ValueError as exc:
        raise ValidationAppError(
            "Invalid workspace id",
            details=[{"field": "X-Workspace-Id", "issue": "invalid_uuid"}],
        ) from exc


async def _listing_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ListingService:
    return ListingService(session)


@router.post("/listings", response_model=ListingResponse, status_code=status.HTTP_201_CREATED)
async def create_listing(
    body: ListingCreate,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ListingService, Depends(_listing_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> ListingResponse:
    ws = _require_workspace(x_workspace_id)
    data = body.model_dump(exclude_unset=True)
    listing = await svc.create_from_product(principal, ws, **data)
    return ListingResponse.model_validate(listing)


@router.get("/listings", response_model=ListingListResponse)
async def list_listings(
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ListingService, Depends(_listing_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status_filter: str | None = Query(default=None, alias="status"),
    product_id: UUID | None = None,
    marketplace_type: str | None = None,
    q: str | None = None,
) -> ListingListResponse:
    ws = _require_workspace(x_workspace_id)
    rows, total = await svc.search(
        principal,
        ws,
        offset=offset,
        limit=limit,
        status=status_filter,
        product_id=product_id,
        marketplace_type=marketplace_type,
        q=q,
    )
    return ListingListResponse(
        items=[ListingResponse.model_validate(r) for r in rows],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/listings/{listing_id}", response_model=ListingResponse)
async def get_listing(
    listing_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ListingService, Depends(_listing_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> ListingResponse:
    ws = _require_workspace(x_workspace_id)
    listing = await svc.get(principal, ws, listing_id)
    return ListingResponse.model_validate(listing)


@router.patch("/listings/{listing_id}", response_model=ListingResponse)
async def update_listing(
    listing_id: UUID,
    body: ListingUpdate,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ListingService, Depends(_listing_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> ListingResponse:
    ws = _require_workspace(x_workspace_id)
    data = body.model_dump(exclude_unset=True)
    content_keys = {
        "description",
        "bullet_points",
        "condition_description",
        "search_keywords",
        "custom_fields",
        "item_specifics",
        "media_refs",
        "marketplace_metadata",
    }
    content_fields = {k: data.pop(k) for k in list(data.keys()) if k in content_keys}
    listing = await svc.update_draft(
        principal, ws, listing_id, content_fields=content_fields or None, **data
    )
    return ListingResponse.model_validate(listing)


@router.post("/listings/{listing_id}/validate", response_model=ListingValidationResponse)
async def validate_listing(
    listing_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ListingService, Depends(_listing_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> ListingValidationResponse:
    ws = _require_workspace(x_workspace_id)
    result = await svc.validate(principal, ws, listing_id)
    _, issues = await svc.get_latest_validation(principal, ws, listing_id)
    return ListingValidationResponse(
        id=result.id,
        listing_id=listing_id,
        passed=result.passed,
        validator_name=result.validator_name,
        summary=result.summary,
        issues=[
            ListingValidationIssueResponse(
                severity=i.severity, code=i.code, field=i.field, message=i.message
            )
            for i in issues
        ],
        created_at=result.created_at,
    )


@router.post("/listings/{listing_id}/submit-for-review", response_model=ListingResponse)
async def submit_for_review(
    listing_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ListingService, Depends(_listing_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> ListingResponse:
    ws = _require_workspace(x_workspace_id)
    listing = await svc.submit_for_review(principal, ws, listing_id)
    return ListingResponse.model_validate(listing)


@router.post("/listings/{listing_id}/approve", response_model=ListingResponse)
async def approve_listing(
    listing_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ListingService, Depends(_listing_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> ListingResponse:
    ws = _require_workspace(x_workspace_id)
    listing = await svc.approve(principal, ws, listing_id)
    return ListingResponse.model_validate(listing)


@router.post("/listings/{listing_id}/schedule", response_model=ListingResponse)
async def schedule_listing(
    listing_id: UUID,
    body: ListingScheduleRequest,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ListingService, Depends(_listing_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> ListingResponse:
    ws = _require_workspace(x_workspace_id)
    listing = await svc.schedule(
        principal, ws, listing_id, scheduled_publish_at=body.scheduled_publish_at
    )
    return ListingResponse.model_validate(listing)


@router.post("/listings/{listing_id}/clone", response_model=ListingResponse, status_code=status.HTTP_201_CREATED)
async def clone_listing(
    listing_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ListingService, Depends(_listing_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> ListingResponse:
    ws = _require_workspace(x_workspace_id)
    listing = await svc.clone(principal, ws, listing_id)
    return ListingResponse.model_validate(listing)


@router.delete("/listings/{listing_id}", response_model=MessageResponse)
async def archive_listing(
    listing_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ListingService, Depends(_listing_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> MessageResponse:
    ws = _require_workspace(x_workspace_id)
    await svc.archive(principal, ws, listing_id)
    return MessageResponse(message="Listing archived")


@router.get("/listings/{listing_id}/preview", response_model=ListingPreviewResponse)
async def preview_listing(
    listing_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ListingService, Depends(_listing_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> ListingPreviewResponse:
    ws = _require_workspace(x_workspace_id)
    data = await svc.preview(principal, ws, listing_id)
    return ListingPreviewResponse(listing=data["listing"], content=data.get("content") or {})


@router.get("/listings/{listing_id}/versions", response_model=list[ListingVersionResponse])
async def listing_versions(
    listing_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ListingService, Depends(_listing_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> list[ListingVersionResponse]:
    ws = _require_workspace(x_workspace_id)
    rows = await svc.list_versions(principal, ws, listing_id)
    return [ListingVersionResponse.model_validate(r) for r in rows]


@router.post(
    "/listing-templates",
    response_model=ListingTemplateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_template(
    body: ListingTemplateCreate,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ListingService, Depends(_listing_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> ListingTemplateResponse:
    ws = _require_workspace(x_workspace_id)
    tpl = await svc.create_template(principal, ws, **body.model_dump(exclude_unset=True))
    return ListingTemplateResponse.model_validate(tpl)


@router.get("/listing-templates", response_model=list[ListingTemplateResponse])
async def list_templates(
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ListingService, Depends(_listing_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> list[ListingTemplateResponse]:
    ws = _require_workspace(x_workspace_id)
    rows = await svc.list_templates(principal, ws)
    return [ListingTemplateResponse.model_validate(r) for r in rows]


@router.get("/listing-templates/{template_id}", response_model=ListingTemplateResponse)
async def get_template(
    template_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ListingService, Depends(_listing_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> ListingTemplateResponse:
    ws = _require_workspace(x_workspace_id)
    rows = await svc.list_templates(principal, ws)
    for r in rows:
        if r.id == template_id:
            return ListingTemplateResponse.model_validate(r)
    from app.domain.listings.exceptions import ListingTemplateNotFoundError

    raise ListingTemplateNotFoundError()


@router.patch("/listing-templates/{template_id}", response_model=ListingTemplateResponse)
async def update_template(
    template_id: UUID,
    body: ListingTemplateUpdate,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ListingService, Depends(_listing_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> ListingTemplateResponse:
    ws = _require_workspace(x_workspace_id)
    tpl = await svc.templates.get(ws, template_id)
    if tpl is None:
        from app.domain.listings.exceptions import ListingTemplateNotFoundError

        raise ListingTemplateNotFoundError()
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(tpl, k, v)
    tpl.updated_by = principal.user_id
    await svc.session.flush()
    return ListingTemplateResponse.model_validate(tpl)


@router.post("/listing-templates/{template_id}/activate", response_model=ListingTemplateResponse)
async def activate_template(
    template_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ListingService, Depends(_listing_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> ListingTemplateResponse:
    ws = _require_workspace(x_workspace_id)
    tpl = await svc.templates.get(ws, template_id)
    if tpl is None:
        from app.domain.listings.exceptions import ListingTemplateNotFoundError

        raise ListingTemplateNotFoundError()
    tpl.is_active = True
    await svc.session.flush()
    return ListingTemplateResponse.model_validate(tpl)


@router.post("/listing-templates/{template_id}/deactivate", response_model=ListingTemplateResponse)
async def deactivate_template(
    template_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ListingService, Depends(_listing_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> ListingTemplateResponse:
    ws = _require_workspace(x_workspace_id)
    tpl = await svc.templates.get(ws, template_id)
    if tpl is None:
        from app.domain.listings.exceptions import ListingTemplateNotFoundError

        raise ListingTemplateNotFoundError()
    tpl.is_active = False
    await svc.session.flush()
    return ListingTemplateResponse.model_validate(tpl)


@router.post(
    "/listings/{listing_id}/apply-template/{template_id}",
    response_model=ListingResponse,
)
async def apply_template(
    listing_id: UUID,
    template_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ListingService, Depends(_listing_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> ListingResponse:
    ws = _require_workspace(x_workspace_id)
    listing = await svc.apply_template(principal, ws, listing_id, template_id)
    return ListingResponse.model_validate(listing)
