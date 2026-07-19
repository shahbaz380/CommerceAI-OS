"""Product catalog API routes."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.catalog.product_service import ProductService
from app.application.identity.authorization import Principal
from app.presentation.api.deps.auth import get_current_principal
from app.presentation.api.deps.common import get_db_session
from app.presentation.schemas.catalog.schemas import (
    AttributeValueCreate,
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    IdentifierCreate,
    IdentifierResponse,
    MediaCreate,
    MediaReorderRequest,
    MediaResponse,
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
    VariantCreate,
    VariantResponse,
    VariantUpdate,
)
from app.presentation.schemas.identity.auth import MessageResponse
from app.shared.exceptions import ValidationAppError

router = APIRouter(tags=["products"])


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


async def _product_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ProductService:
    return ProductService(session)


@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    body: ProductCreate,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ProductService, Depends(_product_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> ProductResponse:
    ws = _require_workspace(x_workspace_id)
    data = body.model_dump(exclude_unset=True)
    auto_sku = data.pop("auto_sku", False)
    product = await svc.create_product(principal, ws, auto_sku=auto_sku, **data)
    return ProductResponse.model_validate(product)


@router.get("/products", response_model=ProductListResponse)
async def list_products(
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ProductService, Depends(_product_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status_filter: str | None = Query(default=None, alias="status"),
    brand: str | None = None,
    product_type: str | None = None,
    sku: str | None = None,
    q: str | None = None,
    category_id: UUID | None = None,
) -> ProductListResponse:
    ws = _require_workspace(x_workspace_id)
    rows, total = await svc.search(
        principal,
        ws,
        offset=offset,
        limit=limit,
        status=status_filter,
        brand=brand,
        product_type=product_type,
        sku=sku,
        q=q,
        category_id=category_id,
    )
    return ProductListResponse(
        items=[ProductResponse.model_validate(r) for r in rows],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ProductService, Depends(_product_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> ProductResponse:
    ws = _require_workspace(x_workspace_id)
    product = await svc.get_product(principal, ws, product_id)
    return ProductResponse.model_validate(product)


@router.patch("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    body: ProductUpdate,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ProductService, Depends(_product_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> ProductResponse:
    ws = _require_workspace(x_workspace_id)
    product = await svc.update_product(principal, ws, product_id, **body.model_dump(exclude_unset=True))
    return ProductResponse.model_validate(product)


@router.post("/products/{product_id}/activate", response_model=ProductResponse)
async def activate_product(
    product_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ProductService, Depends(_product_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> ProductResponse:
    ws = _require_workspace(x_workspace_id)
    product = await svc.transition_status(principal, ws, product_id, "active")
    return ProductResponse.model_validate(product)


@router.post("/products/{product_id}/deactivate", response_model=ProductResponse)
async def deactivate_product(
    product_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ProductService, Depends(_product_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> ProductResponse:
    ws = _require_workspace(x_workspace_id)
    product = await svc.transition_status(principal, ws, product_id, "inactive")
    return ProductResponse.model_validate(product)


@router.delete("/products/{product_id}", response_model=MessageResponse)
async def archive_product(
    product_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ProductService, Depends(_product_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> MessageResponse:
    ws = _require_workspace(x_workspace_id)
    await svc.transition_status(principal, ws, product_id, "archived")
    return MessageResponse(message="Product archived")


@router.post(
    "/products/{product_id}/variants",
    response_model=VariantResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_variant(
    product_id: UUID,
    body: VariantCreate,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ProductService, Depends(_product_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> VariantResponse:
    ws = _require_workspace(x_workspace_id)
    data = body.model_dump(exclude_unset=True)
    metadata = data.pop("metadata", None)
    variant = await svc.add_variant(principal, ws, product_id, metadata=metadata, **data)
    return VariantResponse.model_validate(variant)


@router.patch("/products/{product_id}/variants/{variant_id}", response_model=VariantResponse)
async def update_variant(
    product_id: UUID,
    variant_id: UUID,
    body: VariantUpdate,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ProductService, Depends(_product_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> VariantResponse:
    ws = _require_workspace(x_workspace_id)
    data = body.model_dump(exclude_unset=True)
    if "metadata" in data:
        data["metadata_json"] = data.pop("metadata")
    variant = await svc.update_variant(principal, ws, product_id, variant_id, **data)
    return VariantResponse.model_validate(variant)


@router.post(
    "/products/{product_id}/identifiers",
    response_model=IdentifierResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_identifier(
    product_id: UUID,
    body: IdentifierCreate,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ProductService, Depends(_product_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> IdentifierResponse:
    ws = _require_workspace(x_workspace_id)
    row = await svc.add_identifier(
        principal,
        ws,
        product_id,
        identifier_type=body.identifier_type,
        value=body.value,
        variant_id=body.variant_id,
    )
    return IdentifierResponse.model_validate(row)


@router.post("/products/{product_id}/attributes", status_code=status.HTTP_201_CREATED)
async def add_attribute(
    product_id: UUID,
    body: AttributeValueCreate,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ProductService, Depends(_product_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> dict[str, Any]:
    ws = _require_workspace(x_workspace_id)
    row = await svc.add_attribute_value(
        principal,
        ws,
        product_id,
        attribute_definition_id=body.attribute_definition_id,
        value_text=body.value_text,
        value_json=body.value_json,
        variant_id=body.variant_id,
    )
    return {"id": str(row.id), "product_id": str(product_id)}


@router.post(
    "/products/{product_id}/categories/{category_id}",
    status_code=status.HTTP_201_CREATED,
)
async def assign_category(
    product_id: UUID,
    category_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ProductService, Depends(_product_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
    is_primary: bool = False,
) -> dict[str, Any]:
    ws = _require_workspace(x_workspace_id)
    row = await svc.assign_category(principal, ws, product_id, category_id, is_primary=is_primary)
    return {"id": str(row.id), "product_id": str(product_id), "category_id": str(category_id)}


@router.post(
    "/products/{product_id}/media",
    response_model=MediaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_media(
    product_id: UUID,
    body: MediaCreate,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ProductService, Depends(_product_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> MediaResponse:
    ws = _require_workspace(x_workspace_id)
    data = body.model_dump(exclude_unset=True)
    media = await svc.add_media(principal, ws, product_id, **data)
    return MediaResponse.model_validate(media)


@router.post("/products/{product_id}/media/reorder", response_model=list[MediaResponse])
async def reorder_media(
    product_id: UUID,
    body: MediaReorderRequest,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ProductService, Depends(_product_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> list[MediaResponse]:
    ws = _require_workspace(x_workspace_id)
    rows = await svc.reorder_media(principal, ws, product_id, body.ordered_ids)
    return [MediaResponse.model_validate(r) for r in rows]


@router.post("/product-categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    body: CategoryCreate,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ProductService, Depends(_product_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> CategoryResponse:
    ws = _require_workspace(x_workspace_id)
    cat = await svc.create_category(principal, ws, **body.model_dump(exclude_unset=True))
    return CategoryResponse.model_validate(cat)


@router.get("/product-categories", response_model=list[CategoryResponse])
async def list_categories(
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ProductService, Depends(_product_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> list[CategoryResponse]:
    ws = _require_workspace(x_workspace_id)
    rows = await svc.list_categories(principal, ws)
    return [CategoryResponse.model_validate(r) for r in rows]


@router.get("/product-categories/tree")
async def category_tree(
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ProductService, Depends(_product_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> list[dict[str, Any]]:
    ws = _require_workspace(x_workspace_id)
    rows = await svc.list_categories(principal, ws)
    by_parent: dict[Any, list] = {}
    for r in rows:
        by_parent.setdefault(r.parent_id, []).append(r)

    def build(parent_id: Any) -> list[dict[str, Any]]:
        nodes = []
        for r in by_parent.get(parent_id, []):
            nodes.append(
                {
                    "id": str(r.id),
                    "name": r.name,
                    "slug": r.slug,
                    "path": r.path,
                    "depth": r.depth,
                    "status": r.status,
                    "children": build(r.id),
                }
            )
        return nodes

    return build(None)


@router.get("/product-categories/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ProductService, Depends(_product_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> CategoryResponse:
    ws = _require_workspace(x_workspace_id)
    await svc._require_ws(principal, ws)  # noqa: SLF001
    cat = await svc.categories.get(ws, category_id)
    if cat is None:
        from app.domain.catalog.exceptions import CategoryNotFoundError

        raise CategoryNotFoundError()
    return CategoryResponse.model_validate(cat)


@router.patch("/product-categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    body: CategoryUpdate,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ProductService, Depends(_product_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> CategoryResponse:
    ws = _require_workspace(x_workspace_id)
    cat = await svc.update_category(principal, ws, category_id, **body.model_dump(exclude_unset=True))
    return CategoryResponse.model_validate(cat)


@router.post("/product-categories/{category_id}/activate", response_model=CategoryResponse)
async def activate_category(
    category_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ProductService, Depends(_product_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> CategoryResponse:
    ws = _require_workspace(x_workspace_id)
    cat = await svc.update_category(principal, ws, category_id, status="active")
    return CategoryResponse.model_validate(cat)


@router.post("/product-categories/{category_id}/deactivate", response_model=CategoryResponse)
async def deactivate_category(
    category_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    svc: Annotated[ProductService, Depends(_product_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> CategoryResponse:
    ws = _require_workspace(x_workspace_id)
    cat = await svc.update_category(principal, ws, category_id, status="inactive")
    return CategoryResponse.model_validate(cat)
