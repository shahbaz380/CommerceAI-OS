"""Product catalog application service."""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.identity.authorization import Principal
from app.application.tenancy.tenant_access import TenantAccessService
from app.core.events.bus import DomainEvent, get_event_bus
from app.domain.catalog.enums import CategoryStatus, IdentifierType, MediaStatus, ProductStatus, ProductType
from app.domain.catalog.events import (
    PRODUCT_ACTIVATED,
    PRODUCT_ARCHIVED,
    PRODUCT_CATEGORY_ASSIGNED,
    PRODUCT_CREATED,
    PRODUCT_DEACTIVATED,
    PRODUCT_IMAGE_ADDED,
    PRODUCT_UPDATED,
    PRODUCT_VARIANT_CREATED,
    PRODUCT_VARIANT_UPDATED,
)
from app.domain.catalog.exceptions import (
    CategoryHierarchyError,
    CategoryNotFoundError,
    DuplicatePrimaryImageError,
    DuplicateSKUError,
    MediaNotFoundError,
    ProductNotFoundError,
    ProductVariantNotFoundError,
)
from app.domain.catalog.identifiers import validate_identifier
from app.domain.catalog.lifecycle import assert_product_transition
from app.domain.catalog.sku import auto_generate_sku, validate_sku
from app.domain.tenancy.enums import WorkspaceRole
from app.infrastructure.persistence.models.catalog import (
    ProductAttributeDefinitionModel,
    ProductAttributeValueModel,
    ProductCategoryAssignmentModel,
    ProductCategoryModel,
    ProductIdentifierModel,
    ProductMediaModel,
    ProductModel,
    ProductVariantModel,
)
from app.infrastructure.persistence.repositories.catalog import (
    ProductAttributeRepository,
    ProductCategoryAssignmentRepository,
    ProductCategoryRepository,
    ProductIdentifierRepository,
    ProductMediaRepository,
    ProductRepository,
    ProductVariantRepository,
)
from app.infrastructure.persistence.repositories.tenancy import TenantAuditRepository
from app.shared.exceptions import ValidationAppError

_ALLOWED_MIME = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}


def _slugify(value: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    if len(s) < 2:
        raise ValidationAppError("Slug too short", details=[{"field": "slug", "issue": "too_short"}])
    return s[:200]


class ProductService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.products = ProductRepository(session)
        self.variants = ProductVariantRepository(session)
        self.identifiers = ProductIdentifierRepository(session)
        self.attributes = ProductAttributeRepository(session)
        self.categories = ProductCategoryRepository(session)
        self.assignments = ProductCategoryAssignmentRepository(session)
        self.media = ProductMediaRepository(session)
        self.access = TenantAccessService(session)
        self.audit = TenantAuditRepository(session)
        self.events = get_event_bus()

    async def _require_ws(self, principal: Principal, workspace_id: uuid.UUID, min_role: str = WorkspaceRole.STAFF):
        return await self.access.require_workspace_member(principal, workspace_id, min_role=min_role)

    async def create_product(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        *,
        name: str,
        description: str | None = None,
        brand: str | None = None,
        default_sku: str | None = None,
        auto_sku: bool = False,
        **fields: Any,
    ) -> ProductModel:
        ws, _ = await self._require_ws(principal, workspace_id)
        name = name.strip()
        if len(name) < 1:
            raise ValidationAppError("Product name is required", details=[{"field": "name", "issue": "required"}])
        product_type = fields.get("product_type")
        if product_type is not None:
            product_type = ProductType(product_type).value

        sku = None
        if default_sku:
            sku = validate_sku(default_sku)
        elif auto_sku:
            sku = auto_generate_sku(seed=name[:20] + uuid.uuid4().hex[:6])
        if sku:
            if await self.products.get_by_sku(workspace_id, sku) or await self.variants.get_by_sku(workspace_id, sku):
                raise DuplicateSKUError(sku)
        for key in ("weight_value", "length_value", "width_value", "height_value"):
            val = fields.get(key)
            if val is not None and Decimal(str(val)) < 0:
                raise ValidationAppError(f"{key} cannot be negative", details=[{"field": key, "issue": "negative"}])

        product = ProductModel(
            workspace_id=workspace_id,
            organization_id=ws.organization_id,
            name=name,
            internal_title=fields.get("internal_title") or name,
            description=description,
            brand=brand,
            manufacturer=fields.get("manufacturer"),
            model_number=fields.get("model_number"),
            product_type=product_type,
            condition=fields.get("condition") or "new",
            status=ProductStatus.DRAFT,
            default_sku=sku,
            country_of_origin=fields.get("country_of_origin"),
            weight_value=fields.get("weight_value"),
            weight_unit=fields.get("weight_unit"),
            length_value=fields.get("length_value"),
            width_value=fields.get("width_value"),
            height_value=fields.get("height_value"),
            dimension_unit=fields.get("dimension_unit"),
            tags=fields.get("tags") or [],
            metadata_json=fields.get("metadata") or {},
            created_by=principal.user_id,
            updated_by=principal.user_id,
        )
        await self.products.add(product)
        if sku:
            await self.identifiers.add(
                ProductIdentifierModel(
                    workspace_id=workspace_id,
                    organization_id=ws.organization_id,
                    product_id=product.id,
                    identifier_type=IdentifierType.SKU,
                    value=sku,
                )
            )
        await self.audit.add(
            event_type="product.created",
            message=f"Product created: {name}",
            actor_user_id=principal.user_id,
            organization_id=ws.organization_id,
            workspace_id=workspace_id,
            metadata={"product_id": str(product.id)},
        )
        await self.events.publish(
            DomainEvent(
                name=PRODUCT_CREATED,
                workspace_id=str(workspace_id),
                payload={"product_id": str(product.id)},
            )
        )
        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def get_product(self, principal: Principal, workspace_id: uuid.UUID, product_id: uuid.UUID) -> ProductModel:
        await self._require_ws(principal, workspace_id, min_role=WorkspaceRole.READ_ONLY)
        product = await self.products.get(workspace_id, product_id)
        if product is None:
            raise ProductNotFoundError()
        return product

    async def update_product(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        product_id: uuid.UUID,
        **fields: Any,
    ) -> ProductModel:
        await self._require_ws(principal, workspace_id)
        product = await self.products.get(workspace_id, product_id)
        if product is None:
            raise ProductNotFoundError()
        if "default_sku" in fields and fields["default_sku"] is not None:
            sku = validate_sku(fields["default_sku"])
            existing = await self.products.get_by_sku(workspace_id, sku)
            if existing and existing.id != product.id:
                raise DuplicateSKUError(sku)
            if await self.variants.get_by_sku(workspace_id, sku):
                raise DuplicateSKUError(sku)
            product.default_sku = sku
        if "product_type" in fields and fields["product_type"] is not None:
            product.product_type = ProductType(fields["product_type"]).value
        for key in (
            "name",
            "internal_title",
            "description",
            "brand",
            "manufacturer",
            "model_number",
            "product_type",
            "condition",
            "country_of_origin",
            "weight_value",
            "weight_unit",
            "length_value",
            "width_value",
            "height_value",
            "dimension_unit",
            "tags",
            "metadata_json",
        ):
            if key in fields and fields[key] is not None:
                if key == "metadata":
                    product.metadata_json = fields[key]
                elif key == "metadata_json":
                    product.metadata_json = fields[key]
                else:
                    setattr(product, key, fields[key])
        if "metadata" in fields and fields["metadata"] is not None:
            product.metadata_json = fields["metadata"]
        product.updated_by = principal.user_id
        await self.audit.add(
            event_type="product.updated",
            message="Product updated",
            actor_user_id=principal.user_id,
            organization_id=product.organization_id,
            workspace_id=workspace_id,
            metadata={"product_id": str(product_id)},
        )
        await self.events.publish(
            DomainEvent(name=PRODUCT_UPDATED, workspace_id=str(workspace_id), payload={"product_id": str(product_id)})
        )
        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def transition_status(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        product_id: uuid.UUID,
        target: str,
    ) -> ProductModel:
        await self._require_ws(principal, workspace_id)
        product = await self.products.get(workspace_id, product_id)
        if product is None:
            raise ProductNotFoundError()
        new_status = assert_product_transition(product.status, target)
        product.status = new_status.value
        product.updated_by = principal.user_id
        event = PRODUCT_UPDATED
        if new_status == ProductStatus.ACTIVE:
            event = PRODUCT_ACTIVATED
        elif new_status == ProductStatus.INACTIVE:
            event = PRODUCT_DEACTIVATED
        elif new_status == ProductStatus.ARCHIVED:
            product.archived_at = datetime.now(UTC)
            product.soft_delete()
            event = PRODUCT_ARCHIVED
        elif new_status == ProductStatus.DELETED:
            product.archived_at = datetime.now(UTC)
            product.soft_delete()
            event = PRODUCT_ARCHIVED
        await self.audit.add(
            event_type=f"product.status.{new_status.value}",
            message=f"Product status -> {new_status.value}",
            actor_user_id=principal.user_id,
            organization_id=product.organization_id,
            workspace_id=workspace_id,
            metadata={"product_id": str(product_id)},
        )
        await self.events.publish(
            DomainEvent(name=event, workspace_id=str(workspace_id), payload={"product_id": str(product_id)})
        )
        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def restore_product(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        product_id: uuid.UUID,
    ) -> ProductModel:
        await self._require_ws(principal, workspace_id)
        product = await self.products.get_including_deleted(workspace_id, product_id)
        if product is None:
            raise ProductNotFoundError()
        product.restore()
        product.status = ProductStatus.DRAFT
        product.archived_at = None
        product.updated_by = principal.user_id
        await self.audit.add(
            event_type="product.restored",
            message="Product restored",
            actor_user_id=principal.user_id,
            organization_id=product.organization_id,
            workspace_id=workspace_id,
            metadata={"product_id": str(product_id)},
        )
        await self.events.publish(
            DomainEvent(name=PRODUCT_UPDATED, workspace_id=str(workspace_id), payload={"product_id": str(product_id)})
        )
        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def search(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        **filters: Any,
    ) -> tuple[list[ProductModel], int]:
        await self._require_ws(principal, workspace_id, min_role=WorkspaceRole.READ_ONLY)
        offset = int(filters.pop("offset", 0) or 0)
        limit = int(filters.pop("limit", 50) or 50)
        sort_by = str(filters.pop("sort_by", "created_at") or "created_at")
        sort_order = str(filters.pop("sort_order", "desc") or "desc")
        rows = list(
            await self.products.search(
                workspace_id,
                offset=offset,
                limit=limit,
                sort_by=sort_by,
                sort_order=sort_order,
                **filters,
            )
        )
        total = await self.products.count(workspace_id, **filters)
        return rows, total

    async def add_variant(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        product_id: uuid.UUID,
        *,
        sku: str | None = None,
        title: str | None = None,
        option_values: dict | None = None,
        **fields: Any,
    ) -> ProductVariantModel:
        await self._require_ws(principal, workspace_id)
        product = await self.products.get(workspace_id, product_id)
        if product is None:
            raise ProductNotFoundError()
        sku_val = validate_sku(sku) if sku else auto_generate_sku(seed=f"{product.default_sku or product.name}-{uuid.uuid4().hex[:6]}")
        if await self.products.get_by_sku(workspace_id, sku_val) or await self.variants.get_by_sku(workspace_id, sku_val):
            raise DuplicateSKUError(sku_val)
        variant = ProductVariantModel(
            workspace_id=workspace_id,
            organization_id=product.organization_id,
            product_id=product_id,
            sku=sku_val,
            title=title,
            option_values=option_values or {},
            barcode=fields.get("barcode"),
            mpn=fields.get("mpn"),
            weight_value=fields.get("weight_value"),
            weight_unit=fields.get("weight_unit"),
            length_value=fields.get("length_value"),
            width_value=fields.get("width_value"),
            height_value=fields.get("height_value"),
            dimension_unit=fields.get("dimension_unit"),
            cost_amount=fields.get("cost_amount"),
            cost_currency=fields.get("cost_currency"),
            status=fields.get("status") or "active",
            metadata_json=fields.get("metadata") or {},
        )
        await self.variants.add(variant)
        await self.identifiers.add(
            ProductIdentifierModel(
                workspace_id=workspace_id,
                organization_id=product.organization_id,
                product_id=product_id,
                variant_id=variant.id,
                identifier_type=IdentifierType.SKU,
                value=sku_val,
            )
        )
        await self.audit.add(
            event_type="product.variant.created",
            message=f"Variant created: {sku_val}",
            actor_user_id=principal.user_id,
            organization_id=product.organization_id,
            workspace_id=workspace_id,
            metadata={"product_id": str(product_id), "variant_id": str(variant.id)},
        )
        await self.events.publish(
            DomainEvent(
                name=PRODUCT_VARIANT_CREATED,
                workspace_id=str(workspace_id),
                payload={"product_id": str(product_id), "variant_id": str(variant.id)},
            )
        )
        await self.session.flush()
        return variant

    async def update_variant(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        product_id: uuid.UUID,
        variant_id: uuid.UUID,
        **fields: Any,
    ) -> ProductVariantModel:
        await self._require_ws(principal, workspace_id)
        variant = await self.variants.get(workspace_id, product_id, variant_id)
        if variant is None:
            raise ProductVariantNotFoundError()
        if "sku" in fields and fields["sku"] is not None:
            sku_val = validate_sku(fields["sku"])
            existing = await self.variants.get_by_sku(workspace_id, sku_val)
            if existing and existing.id != variant.id:
                raise DuplicateSKUError(sku_val)
            if await self.products.get_by_sku(workspace_id, sku_val):
                raise DuplicateSKUError(sku_val)
            variant.sku = sku_val
        for key in (
            "title",
            "option_values",
            "barcode",
            "mpn",
            "weight_value",
            "weight_unit",
            "length_value",
            "width_value",
            "height_value",
            "dimension_unit",
            "cost_amount",
            "cost_currency",
            "status",
            "metadata_json",
        ):
            if key in fields and fields[key] is not None:
                setattr(variant, key if key != "metadata" else "metadata_json", fields[key])
        if "metadata" in fields and fields["metadata"] is not None:
            variant.metadata_json = fields["metadata"]
        await self.events.publish(
            DomainEvent(
                name=PRODUCT_VARIANT_UPDATED,
                workspace_id=str(workspace_id),
                payload={"product_id": str(product_id), "variant_id": str(variant_id)},
            )
        )
        await self.session.flush()
        return variant

    async def add_identifier(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        product_id: uuid.UUID,
        *,
        identifier_type: str,
        value: str,
        variant_id: uuid.UUID | None = None,
    ) -> ProductIdentifierModel:
        await self._require_ws(principal, workspace_id)
        product = await self.products.get(workspace_id, product_id)
        if product is None:
            raise ProductNotFoundError()
        normalized = validate_identifier(identifier_type, value)
        row = ProductIdentifierModel(
            workspace_id=workspace_id,
            organization_id=product.organization_id,
            product_id=product_id,
            variant_id=variant_id,
            identifier_type=identifier_type,
            value=normalized,
        )
        await self.identifiers.add(row)
        await self.session.flush()
        return row

    async def create_attribute_definition(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        *,
        code: str,
        name: str,
        data_type: str,
        is_required: bool = False,
        is_searchable: bool = False,
        is_variant_defining: bool = False,
        enum_options: list[Any] | None = None,
        marketplace_mapping: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ProductAttributeDefinitionModel:
        ws, _ = await self._require_ws(principal, workspace_id, min_role=WorkspaceRole.MANAGER)
        code_val = code.strip().lower()
        if not code_val:
            raise ValidationAppError("Attribute code is required", details=[{"field": "code", "issue": "required"}])
        if await self.attributes.get_definition_by_code(workspace_id, code_val):
            raise ValidationAppError("Attribute code exists", details=[{"field": "code", "issue": "duplicate"}])
        row = ProductAttributeDefinitionModel(
            workspace_id=workspace_id,
            organization_id=ws.organization_id,
            code=code_val,
            name=name.strip(),
            data_type=data_type,
            is_required=is_required,
            is_searchable=is_searchable,
            is_variant_defining=is_variant_defining,
            enum_options=enum_options,
            marketplace_mapping=marketplace_mapping,
            metadata_json=metadata or {},
        )
        await self.attributes.add_definition(row)
        await self.session.flush()
        return row

    async def list_attribute_definitions(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
    ) -> list[ProductAttributeDefinitionModel]:
        await self._require_ws(principal, workspace_id, min_role=WorkspaceRole.READ_ONLY)
        return list(await self.attributes.list_definitions(workspace_id))

    async def add_attribute_value(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        product_id: uuid.UUID,
        *,
        attribute_definition_id: uuid.UUID,
        value_text: str | None = None,
        value_json: Any = None,
        variant_id: uuid.UUID | None = None,
    ) -> ProductAttributeValueModel:
        await self._require_ws(principal, workspace_id)
        product = await self.products.get(workspace_id, product_id)
        if product is None:
            raise ProductNotFoundError()
        definition = await self.attributes.get_definition(workspace_id, attribute_definition_id)
        if definition is None:
            raise ValidationAppError("Attribute definition not found", details=[{"field": "attribute_definition_id"}])
        row = ProductAttributeValueModel(
            workspace_id=workspace_id,
            organization_id=product.organization_id,
            product_id=product_id,
            variant_id=variant_id,
            attribute_definition_id=attribute_definition_id,
            value_text=value_text,
            value_json=value_json,
        )
        await self.attributes.add_value(row)
        await self.session.flush()
        return row

    async def assign_tags(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        product_id: uuid.UUID,
        *,
        tags: list[str],
    ) -> ProductModel:
        await self._require_ws(principal, workspace_id)
        product = await self.products.get(workspace_id, product_id)
        if product is None:
            raise ProductNotFoundError()
        normalized = [str(tag).strip() for tag in tags if str(tag).strip()]
        product.tags = list(dict.fromkeys(normalized))
        product.updated_by = principal.user_id
        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def assign_category(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        product_id: uuid.UUID,
        category_id: uuid.UUID,
        *,
        is_primary: bool = False,
    ) -> ProductCategoryAssignmentModel:
        await self._require_ws(principal, workspace_id)
        product = await self.products.get(workspace_id, product_id)
        if product is None:
            raise ProductNotFoundError()
        category = await self.categories.get(workspace_id, category_id)
        if category is None:
            raise CategoryNotFoundError()
        if await self.assignments.exists(product_id, category_id):
            raise ValidationAppError("Category already assigned", details=[{"field": "category_id", "issue": "duplicate"}])
        row = ProductCategoryAssignmentModel(
            workspace_id=workspace_id,
            organization_id=product.organization_id,
            product_id=product_id,
            category_id=category_id,
            is_primary=is_primary,
        )
        await self.assignments.add(row)
        await self.events.publish(
            DomainEvent(
                name=PRODUCT_CATEGORY_ASSIGNED,
                workspace_id=str(workspace_id),
                payload={"product_id": str(product_id), "category_id": str(category_id)},
            )
        )
        await self.session.flush()
        return row

    async def add_media(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        product_id: uuid.UUID,
        *,
        url: str,
        is_primary: bool = False,
        mime_type: str | None = None,
        variant_id: uuid.UUID | None = None,
        **fields: Any,
    ) -> ProductMediaModel:
        await self._require_ws(principal, workspace_id)
        product = await self.products.get(workspace_id, product_id)
        if product is None:
            raise ProductNotFoundError()
        if mime_type and mime_type not in _ALLOWED_MIME:
            raise ValidationAppError(
                "Unsupported MIME type",
                details=[{"field": "mime_type", "issue": mime_type}],
            )
        if is_primary:
            existing = await self.media.list_for_product(workspace_id, product_id)
            for m in existing:
                same_scope = (variant_id is None and m.variant_id is None) or (
                    variant_id is not None and m.variant_id == variant_id
                )
                if same_scope and m.is_primary:
                    raise DuplicatePrimaryImageError()
        media = ProductMediaModel(
            workspace_id=workspace_id,
            organization_id=product.organization_id,
            product_id=product_id,
            variant_id=variant_id,
            url=url,
            storage_key=fields.get("storage_key"),
            file_name=fields.get("file_name"),
            mime_type=mime_type,
            file_size=fields.get("file_size"),
            width=fields.get("width"),
            height=fields.get("height"),
            alt_text=fields.get("alt_text"),
            sort_order=int(fields.get("sort_order") or 0),
            is_primary=is_primary,
            status=MediaStatus.ACTIVE,
            checksum=fields.get("checksum"),
            metadata_json=fields.get("metadata") or {},
        )
        await self.media.add(media)
        await self.events.publish(
            DomainEvent(
                name=PRODUCT_IMAGE_ADDED,
                workspace_id=str(workspace_id),
                payload={"product_id": str(product_id), "media_id": str(media.id)},
            )
        )
        await self.session.flush()
        return media

    async def reorder_media(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        product_id: uuid.UUID,
        ordered_ids: list[uuid.UUID],
    ) -> list[ProductMediaModel]:
        await self._require_ws(principal, workspace_id)
        rows = list(await self.media.list_for_product(workspace_id, product_id))
        by_id = {r.id: r for r in rows}
        for idx, mid in enumerate(ordered_ids):
            if mid not in by_id:
                raise MediaNotFoundError()
            by_id[mid].sort_order = idx
        await self.session.flush()
        return list(await self.media.list_for_product(workspace_id, product_id))

    # --- categories ---
    async def create_category(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        *,
        name: str,
        slug: str | None = None,
        parent_id: uuid.UUID | None = None,
        description: str | None = None,
        sort_order: int = 0,
    ) -> ProductCategoryModel:
        ws, _ = await self._require_ws(principal, workspace_id, min_role=WorkspaceRole.MANAGER)
        slug_val = _slugify(slug or name)
        if await self.categories.get_by_slug(workspace_id, slug_val):
            raise ValidationAppError("Category slug exists", details=[{"field": "slug", "issue": "duplicate"}])
        depth = 0
        path = f"/{slug_val}"
        if parent_id:
            parent = await self.categories.get(workspace_id, parent_id)
            if parent is None:
                raise CategoryNotFoundError("Parent category not found")
            depth = parent.depth + 1
            path = f"{parent.path.rstrip('/')}/{slug_val}"
        cat = ProductCategoryModel(
            workspace_id=workspace_id,
            organization_id=ws.organization_id,
            parent_id=parent_id,
            name=name.strip(),
            slug=slug_val,
            description=description,
            path=path,
            depth=depth,
            status=CategoryStatus.ACTIVE,
            sort_order=sort_order,
            metadata_json={},
            marketplace_mapping={},
        )
        await self.categories.add(cat)
        await self.session.flush()
        return cat

    async def update_category(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        category_id: uuid.UUID,
        **fields: Any,
    ) -> ProductCategoryModel:
        await self._require_ws(principal, workspace_id, min_role=WorkspaceRole.MANAGER)
        cat = await self.categories.get(workspace_id, category_id)
        if cat is None:
            raise CategoryNotFoundError()
        if "parent_id" in fields and fields["parent_id"] is not None:
            new_parent_id = fields["parent_id"]
            if new_parent_id == category_id:
                raise CategoryHierarchyError("Category cannot be its own parent")
            # prevent cycles: walk parents
            cursor = await self.categories.get(workspace_id, new_parent_id)
            while cursor is not None:
                if cursor.id == category_id:
                    raise CategoryHierarchyError("Circular category reference")
                if cursor.parent_id is None:
                    break
                cursor = await self.categories.get(workspace_id, cursor.parent_id)
            parent = await self.categories.get(workspace_id, new_parent_id)
            if parent is None:
                raise CategoryNotFoundError("Parent category not found")
            cat.parent_id = new_parent_id
            cat.depth = parent.depth + 1
            cat.path = f"{parent.path.rstrip('/')}/{cat.slug}"
        for key in ("name", "description", "sort_order", "status", "metadata_json", "marketplace_mapping"):
            if key in fields and fields[key] is not None:
                setattr(cat, key, fields[key])
        await self.session.flush()
        return cat

    async def list_categories(self, principal: Principal, workspace_id: uuid.UUID) -> list[ProductCategoryModel]:
        await self._require_ws(principal, workspace_id, min_role=WorkspaceRole.READ_ONLY)
        return list(await self.categories.list_all(workspace_id))
