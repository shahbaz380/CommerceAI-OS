"""Listing management application service."""

from __future__ import annotations

import copy
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.identity.authorization import Principal
from app.application.tenancy.tenant_access import TenantAccessService
from app.core.events.bus import DomainEvent, get_event_bus
from app.domain.listings.enums import ListingFormat, ListingStatus, ValidationSeverity
from app.domain.listings.events import (
    LISTING_APPROVED,
    LISTING_ARCHIVED,
    LISTING_DRAFT_CREATED,
    LISTING_SCHEDULED,
    LISTING_STATUS_CHANGED,
    LISTING_UPDATED,
    LISTING_VALIDATED,
    LISTING_VERSION_CREATED,
)
from app.domain.listings.exceptions import (
    ListingApprovalError,
    ListingNotFoundError,
    ListingScheduleError,
    ListingTemplateNotFoundError,
    ListingValidationError,
    MarketplaceConnectionMismatchError,
)
from app.domain.listings.lifecycle import assert_listing_transition
from app.domain.tenancy.enums import WorkspaceRole
from app.infrastructure.marketplace.listing_validation.base import ValidationRegistry
from app.infrastructure.marketplace.listing_validation.ebay import EbayListingPolicyValidator
from app.infrastructure.persistence.models.listings import (
    ListingContentModel,
    ListingMarketplaceMappingModel,
    ListingModel,
    ListingStatusHistoryModel,
    ListingTemplateModel,
    ListingValidationIssueModel,
    ListingValidationResultModel,
    ListingVersionModel,
)
from app.infrastructure.persistence.repositories.catalog import ProductRepository, ProductVariantRepository
from app.infrastructure.persistence.repositories.listings import (
    ListingContentRepository,
    ListingMappingRepository,
    ListingRepository,
    ListingStatusHistoryRepository,
    ListingTemplateRepository,
    ListingValidationRepository,
    ListingVersionRepository,
)
from app.infrastructure.persistence.repositories.marketplace import MarketplaceConnectionRepository
from app.infrastructure.persistence.repositories.tenancy import TenantAuditRepository
from app.shared.exceptions import ValidationAppError


class ListingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.listings = ListingRepository(session)
        self.content = ListingContentRepository(session)
        self.templates = ListingTemplateRepository(session)
        self.version_repo = ListingVersionRepository(session)
        self.validations = ListingValidationRepository(session)
        self.history = ListingStatusHistoryRepository(session)
        self.mappings = ListingMappingRepository(session)
        self.products = ProductRepository(session)
        self.variants = ProductVariantRepository(session)
        self.connections = MarketplaceConnectionRepository(session)
        self.access = TenantAccessService(session)
        self.audit = TenantAuditRepository(session)
        self.events = get_event_bus()
        self.validators = ValidationRegistry()
        self.validators.register("ebay_policy", EbayListingPolicyValidator())

    async def _require_ws(self, principal: Principal, workspace_id: uuid.UUID, min_role: str = WorkspaceRole.STAFF):
        return await self.access.require_workspace_member(principal, workspace_id, min_role=min_role)

    def _listing_snapshot(self, listing: ListingModel, content: ListingContentModel | None) -> dict[str, Any]:
        return {
            "listing": {
                "internal_title": listing.internal_title,
                "marketplace_title": listing.marketplace_title,
                "subtitle": listing.subtitle,
                "listing_format": listing.listing_format,
                "condition": listing.condition,
                "category_id": str(listing.category_id) if listing.category_id else None,
                "currency": listing.currency,
                "price_amount": str(listing.price_amount) if listing.price_amount is not None else None,
                "quantity": listing.quantity,
                "status": listing.status,
                "marketplace_type": listing.marketplace_type,
                "metadata": listing.metadata_json,
            },
            "content": {
                "description": content.description if content else None,
                "bullet_points": content.bullet_points if content else None,
                "condition_description": content.condition_description if content else None,
                "search_keywords": content.search_keywords if content else None,
                "custom_fields": content.custom_fields if content else None,
                "item_specifics": content.item_specifics if content else None,
                "media_refs": content.media_refs if content else None,
                "marketplace_metadata": content.marketplace_metadata if content else None,
            }
            if content
            else {},
        }

    async def _record_version(
        self,
        listing: ListingModel,
        content: ListingContentModel | None,
        principal: Principal,
        *,
        reason: str | None = None,
        changed_fields: list[str] | None = None,
    ) -> ListingVersionModel:
        version_no = await self.version_repo.next_version_number(listing.id)
        row = ListingVersionModel(
            workspace_id=listing.workspace_id,
            organization_id=listing.organization_id,
            listing_id=listing.id,
            version_number=version_no,
            snapshot=self._listing_snapshot(listing, content),
            changed_fields=changed_fields,
            change_reason=reason,
            changed_by=principal.user_id,
        )
        await self.version_repo.add(row)
        await self.events.publish(
            DomainEvent(
                name=LISTING_VERSION_CREATED,
                workspace_id=str(listing.workspace_id),
                payload={"listing_id": str(listing.id), "version": version_no},
            )
        )
        return row

    async def _record_status(
        self,
        listing: ListingModel,
        principal: Principal,
        *,
        from_status: str | None,
        to_status: str,
        reason: str | None = None,
    ) -> None:
        await self.history.add(
            ListingStatusHistoryModel(
                workspace_id=listing.workspace_id,
                organization_id=listing.organization_id,
                listing_id=listing.id,
                from_status=from_status,
                to_status=to_status,
                actor_user_id=principal.user_id,
                reason=reason,
            )
        )

    async def create_from_product(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        *,
        product_id: uuid.UUID,
        product_variant_id: uuid.UUID | None = None,
        marketplace_connection_id: uuid.UUID | None = None,
        marketplace_type: str | None = None,
        internal_title: str | None = None,
        marketplace_title: str | None = None,
        listing_format: str = ListingFormat.FIXED_PRICE,
        currency: str = "USD",
        price_amount: Decimal | None = None,
        quantity: int | None = None,
        description: str | None = None,
        category_id: uuid.UUID | None = None,
        condition: str | None = None,
        **fields: Any,
    ) -> ListingModel:
        ws, _ = await self._require_ws(principal, workspace_id)
        product = await self.products.get(workspace_id, product_id)
        if product is None:
            from app.domain.catalog.exceptions import ProductNotFoundError

            raise ProductNotFoundError()
        if product_variant_id:
            variant = await self.variants.get(workspace_id, product_id, product_variant_id)
            if variant is None:
                from app.domain.catalog.exceptions import ProductVariantNotFoundError

                raise ProductVariantNotFoundError()
        if marketplace_connection_id:
            conn = await self.connections.get_for_workspace(workspace_id, marketplace_connection_id)
            if conn is None:
                raise MarketplaceConnectionMismatchError("Marketplace connection not found in workspace")
            marketplace_type = marketplace_type or conn.channel

        if price_amount is not None and Decimal(str(price_amount)) < 0:
            raise ValidationAppError("Price cannot be negative", details=[{"field": "price_amount"}])
        if quantity is not None and int(quantity) < 0:
            raise ValidationAppError("Quantity cannot be negative", details=[{"field": "quantity"}])

        title = (internal_title or product.internal_title or product.name).strip()
        listing = ListingModel(
            workspace_id=workspace_id,
            organization_id=ws.organization_id,
            product_id=product_id,
            product_variant_id=product_variant_id,
            marketplace_connection_id=marketplace_connection_id,
            marketplace_type=marketplace_type,
            internal_title=title,
            marketplace_title=marketplace_title or title,
            subtitle=fields.get("subtitle"),
            listing_format=listing_format,
            condition=condition or product.condition,
            category_id=category_id,
            currency=(currency or "USD").upper(),
            price_amount=price_amount,
            quantity=quantity,
            status=ListingStatus.DRAFT,
            metadata_json=fields.get("metadata") or {},
            created_by=principal.user_id,
            updated_by=principal.user_id,
        )
        await self.listings.add(listing)
        content = ListingContentModel(
            workspace_id=workspace_id,
            organization_id=ws.organization_id,
            listing_id=listing.id,
            description=description or product.description,
            bullet_points=fields.get("bullet_points") or [],
            condition_description=fields.get("condition_description"),
            search_keywords=fields.get("search_keywords") or [],
            custom_fields=fields.get("custom_fields") or {},
            item_specifics=fields.get("item_specifics") or {},
            media_refs=fields.get("media_refs") or [],
            marketplace_metadata=fields.get("marketplace_metadata") or {},
        )
        await self.content.add(content)
        if marketplace_connection_id:
            await self.mappings.add(
                ListingMarketplaceMappingModel(
                    workspace_id=workspace_id,
                    organization_id=ws.organization_id,
                    listing_id=listing.id,
                    marketplace_connection_id=marketplace_connection_id,
                    marketplace_type=marketplace_type or "unknown",
                    metadata_json={},
                )
            )
        await self._record_version(listing, content, principal, reason="created")
        await self._record_status(listing, principal, from_status=None, to_status=ListingStatus.DRAFT, reason="created")
        await self.audit.add(
            event_type="listing.created",
            message=f"Listing draft created: {title}",
            actor_user_id=principal.user_id,
            organization_id=ws.organization_id,
            workspace_id=workspace_id,
            metadata={"listing_id": str(listing.id), "product_id": str(product_id)},
        )
        await self.events.publish(
            DomainEvent(
                name=LISTING_DRAFT_CREATED,
                workspace_id=str(workspace_id),
                payload={"listing_id": str(listing.id)},
            )
        )
        await self.session.flush()
        await self.session.refresh(listing)
        return listing

    async def get(self, principal: Principal, workspace_id: uuid.UUID, listing_id: uuid.UUID) -> ListingModel:
        await self._require_ws(principal, workspace_id, min_role=WorkspaceRole.READ_ONLY)
        listing = await self.listings.get(workspace_id, listing_id)
        if listing is None:
            raise ListingNotFoundError()
        return listing

    async def search(
        self, principal: Principal, workspace_id: uuid.UUID, **filters: Any
    ) -> tuple[list[ListingModel], int]:
        await self._require_ws(principal, workspace_id, min_role=WorkspaceRole.READ_ONLY)
        offset = int(filters.pop("offset", 0) or 0)
        limit = int(filters.pop("limit", 50) or 50)
        rows = list(await self.listings.search(workspace_id, offset=offset, limit=limit, **filters))
        total = await self.listings.count(workspace_id, **filters)
        return rows, total

    async def update_draft(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        listing_id: uuid.UUID,
        *,
        content_fields: dict[str, Any] | None = None,
        **fields: Any,
    ) -> ListingModel:
        await self._require_ws(principal, workspace_id)
        listing = await self.listings.get(workspace_id, listing_id)
        if listing is None:
            raise ListingNotFoundError()
        if listing.status in {ListingStatus.PUBLISHING, ListingStatus.ARCHIVED}:
            raise ValidationAppError(
                "Listing cannot be edited in current status",
                details=[{"field": "status", "issue": listing.status}],
            )
        changed: list[str] = []
        for key in (
            "internal_title",
            "marketplace_title",
            "subtitle",
            "listing_format",
            "condition",
            "category_id",
            "currency",
            "price_amount",
            "quantity",
            "marketplace_type",
            "marketplace_connection_id",
            "metadata_json",
            "scheduled_publish_at",
        ):
            if key in fields and fields[key] is not None:
                if key == "price_amount" and Decimal(str(fields[key])) < 0:
                    raise ValidationAppError("Price cannot be negative")
                if key == "quantity" and int(fields[key]) < 0:
                    raise ValidationAppError("Quantity cannot be negative")
                if key == "currency":
                    fields[key] = str(fields[key]).upper()
                if key == "metadata":
                    listing.metadata_json = fields[key]
                else:
                    setattr(listing, key if key != "metadata" else "metadata_json", fields[key])
                changed.append(key)
        if "metadata" in fields and fields["metadata"] is not None:
            listing.metadata_json = fields["metadata"]
            changed.append("metadata")

        content = await self.content.get_by_listing(workspace_id, listing_id)
        if content is None:
            content = ListingContentModel(
                workspace_id=workspace_id,
                organization_id=listing.organization_id,
                listing_id=listing.id,
            )
            await self.content.add(content)
        if content_fields:
            for key in (
                "description",
                "bullet_points",
                "condition_description",
                "search_keywords",
                "custom_fields",
                "item_specifics",
                "media_refs",
                "marketplace_metadata",
            ):
                if key in content_fields and content_fields[key] is not None:
                    setattr(content, key, content_fields[key])
                    changed.append(f"content.{key}")

        listing.updated_by = principal.user_id
        await self._record_version(listing, content, principal, reason="update", changed_fields=changed)
        await self.audit.add(
            event_type="listing.updated",
            message="Listing updated",
            actor_user_id=principal.user_id,
            organization_id=listing.organization_id,
            workspace_id=workspace_id,
            metadata={"listing_id": str(listing_id), "changed": changed},
        )
        await self.events.publish(
            DomainEvent(name=LISTING_UPDATED, workspace_id=str(workspace_id), payload={"listing_id": str(listing_id)})
        )
        await self.session.flush()
        return listing

    def _listing_dict(self, listing: ListingModel) -> dict[str, Any]:
        return {
            "internal_title": listing.internal_title,
            "marketplace_title": listing.marketplace_title,
            "subtitle": listing.subtitle,
            "listing_format": listing.listing_format,
            "condition": listing.condition,
            "category_id": str(listing.category_id) if listing.category_id else None,
            "currency": listing.currency,
            "price_amount": listing.price_amount,
            "quantity": listing.quantity,
            "status": listing.status,
            "marketplace_type": listing.marketplace_type,
        }

    async def validate(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        listing_id: uuid.UUID,
        *,
        include_ebay_policy: bool = True,
    ) -> ListingValidationResultModel:
        await self._require_ws(principal, workspace_id)
        listing = await self.listings.get(workspace_id, listing_id)
        if listing is None:
            raise ListingNotFoundError()
        content = await self.content.get_by_listing(workspace_id, listing_id)
        content_dict = {
            "description": content.description if content else None,
            "bullet_points": content.bullet_points if content else None,
        }
        keys = ["default"]
        if include_ebay_policy and (listing.marketplace_type or "").lower() in {"ebay", ""}:
            keys.append("ebay_policy")
        result = self.validators.validate_all(self._listing_dict(listing), content_dict, keys=keys)
        row = await self.validations.add_result(
            ListingValidationResultModel(
                workspace_id=workspace_id,
                organization_id=listing.organization_id,
                listing_id=listing.id,
                passed=result.passed,
                validator_name=result.validator_name,
                summary=result.summary,
            )
        )
        for issue in result.issues:
            await self.validations.add_issue(
                ListingValidationIssueModel(
                    validation_result_id=row.id,
                    severity=issue.severity,
                    code=issue.code,
                    field=issue.field,
                    message=issue.message,
                )
            )
        listing.last_validated_at = datetime.now(UTC)
        listing.validation_passed = result.passed
        await self.events.publish(
            DomainEvent(
                name=LISTING_VALIDATED,
                workspace_id=str(workspace_id),
                payload={"listing_id": str(listing_id), "passed": result.passed},
            )
        )
        await self.session.flush()
        return row

    async def _transition(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        listing_id: uuid.UUID,
        target: ListingStatus,
        *,
        reason: str | None = None,
        min_role: str = WorkspaceRole.STAFF,
    ) -> ListingModel:
        await self._require_ws(principal, workspace_id, min_role=min_role)
        listing = await self.listings.get(workspace_id, listing_id)
        if listing is None:
            raise ListingNotFoundError()
        previous = listing.status
        new_status = assert_listing_transition(previous, target)
        listing.status = new_status.value
        listing.updated_by = principal.user_id
        await self._record_status(listing, principal, from_status=previous, to_status=new_status.value, reason=reason)
        await self.events.publish(
            DomainEvent(
                name=LISTING_STATUS_CHANGED,
                workspace_id=str(workspace_id),
                payload={"listing_id": str(listing_id), "from": previous, "to": new_status.value},
            )
        )
        await self.session.flush()
        await self.session.refresh(listing)
        return listing

    async def submit_for_review(self, principal: Principal, workspace_id: uuid.UUID, listing_id: uuid.UUID) -> ListingModel:
        validation = await self.validate(principal, workspace_id, listing_id)
        if not validation.passed:
            issues = await self.validations.list_issues(validation.id)
            raise ListingValidationError(
                details=[{"field": i.field, "issue": i.code, "message": i.message} for i in issues if i.severity == ValidationSeverity.ERROR]
            )
        return await self._transition(
            principal, workspace_id, listing_id, ListingStatus.READY_FOR_REVIEW, reason="submit_for_review"
        )

    async def approve(self, principal: Principal, workspace_id: uuid.UUID, listing_id: uuid.UUID) -> ListingModel:
        listing = await self.listings.get(workspace_id, listing_id)
        if listing is None:
            raise ListingNotFoundError()
        validation = await self.validate(principal, workspace_id, listing_id)
        if not validation.passed:
            raise ListingApprovalError("Listing has blocking validation errors")
        if not listing.category_id:
            # allow with warning path already in validator; still block approval if policy wants category
            # keep soft: only block if validation errors
            pass
        listing = await self._transition(
            principal,
            workspace_id,
            listing_id,
            ListingStatus.APPROVED,
            reason="approved",
            min_role=WorkspaceRole.MANAGER,
        )
        await self.events.publish(
            DomainEvent(name=LISTING_APPROVED, workspace_id=str(workspace_id), payload={"listing_id": str(listing_id)})
        )
        await self.audit.add(
            event_type="listing.approved",
            message="Listing approved",
            actor_user_id=principal.user_id,
            organization_id=listing.organization_id,
            workspace_id=workspace_id,
            metadata={"listing_id": str(listing_id)},
        )
        await self.session.flush()
        return listing

    async def schedule(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        listing_id: uuid.UUID,
        *,
        scheduled_publish_at: datetime,
    ) -> ListingModel:
        if scheduled_publish_at.tzinfo is None:
            scheduled_publish_at = scheduled_publish_at.replace(tzinfo=UTC)
        if scheduled_publish_at <= datetime.now(UTC):
            raise ListingScheduleError("Scheduled time must be in the future")
        listing = await self.listings.get(workspace_id, listing_id)
        if listing is None:
            raise ListingNotFoundError()
        if listing.status != ListingStatus.APPROVED:
            # allow transition path approved -> scheduled only
            pass
        listing.scheduled_publish_at = scheduled_publish_at
        listing = await self._transition(
            principal,
            workspace_id,
            listing_id,
            ListingStatus.SCHEDULED,
            reason="scheduled",
            min_role=WorkspaceRole.MANAGER,
        )
        await self.events.publish(
            DomainEvent(
                name=LISTING_SCHEDULED,
                workspace_id=str(workspace_id),
                payload={"listing_id": str(listing_id), "at": scheduled_publish_at.isoformat()},
            )
        )
        await self.session.flush()
        return listing

    async def archive(self, principal: Principal, workspace_id: uuid.UUID, listing_id: uuid.UUID) -> ListingModel:
        listing = await self._transition(
            principal, workspace_id, listing_id, ListingStatus.ARCHIVED, reason="archived"
        )
        listing.archived_at = datetime.now(UTC)
        listing.soft_delete()
        await self.events.publish(
            DomainEvent(name=LISTING_ARCHIVED, workspace_id=str(workspace_id), payload={"listing_id": str(listing_id)})
        )
        await self.session.flush()
        return listing

    async def clone(self, principal: Principal, workspace_id: uuid.UUID, listing_id: uuid.UUID) -> ListingModel:
        await self._require_ws(principal, workspace_id)
        source = await self.listings.get(workspace_id, listing_id)
        if source is None:
            raise ListingNotFoundError()
        content = await self.content.get_by_listing(workspace_id, listing_id)
        clone = ListingModel(
            workspace_id=workspace_id,
            organization_id=source.organization_id,
            product_id=source.product_id,
            product_variant_id=source.product_variant_id,
            marketplace_connection_id=source.marketplace_connection_id,
            marketplace_type=source.marketplace_type,
            internal_title=f"{source.internal_title} (Copy)",
            marketplace_title=source.marketplace_title,
            subtitle=source.subtitle,
            listing_format=source.listing_format,
            condition=source.condition,
            category_id=source.category_id,
            currency=source.currency,
            price_amount=source.price_amount,
            quantity=source.quantity,
            status=ListingStatus.DRAFT,
            metadata_json=copy.deepcopy(source.metadata_json or {}),
            created_by=principal.user_id,
            updated_by=principal.user_id,
        )
        await self.listings.add(clone)
        if content:
            await self.content.add(
                ListingContentModel(
                    workspace_id=workspace_id,
                    organization_id=source.organization_id,
                    listing_id=clone.id,
                    description=content.description,
                    bullet_points=copy.deepcopy(content.bullet_points),
                    condition_description=content.condition_description,
                    search_keywords=copy.deepcopy(content.search_keywords),
                    custom_fields=copy.deepcopy(content.custom_fields),
                    item_specifics=copy.deepcopy(content.item_specifics),
                    media_refs=copy.deepcopy(content.media_refs),
                    marketplace_metadata=copy.deepcopy(content.marketplace_metadata),
                )
            )
        new_content = await self.content.get_by_listing(workspace_id, clone.id)
        await self._record_version(clone, new_content, principal, reason="cloned")
        await self._record_status(clone, principal, from_status=None, to_status=ListingStatus.DRAFT, reason="cloned")
        await self.session.flush()
        return clone

    async def preview(self, principal: Principal, workspace_id: uuid.UUID, listing_id: uuid.UUID) -> dict[str, Any]:
        listing = await self.get(principal, workspace_id, listing_id)
        content = await self.content.get_by_listing(workspace_id, listing_id)
        return self._listing_snapshot(listing, content)

    async def list_versions(
        self, principal: Principal, workspace_id: uuid.UUID, listing_id: uuid.UUID
    ) -> list[ListingVersionModel]:
        await self.get(principal, workspace_id, listing_id)
        return list(await self.version_repo.list_for_listing(workspace_id, listing_id))

    # templates
    async def create_template(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        *,
        name: str,
        **fields: Any,
    ) -> ListingTemplateModel:
        ws, _ = await self._require_ws(principal, workspace_id, min_role=WorkspaceRole.MANAGER)
        tpl = ListingTemplateModel(
            workspace_id=workspace_id,
            organization_id=ws.organization_id,
            name=name.strip(),
            description=fields.get("description"),
            marketplace_type=fields.get("marketplace_type"),
            listing_format=fields.get("listing_format") or ListingFormat.FIXED_PRICE,
            title_template=fields.get("title_template"),
            description_template=fields.get("description_template"),
            default_condition=fields.get("default_condition"),
            default_category_id=fields.get("default_category_id"),
            default_metadata=fields.get("default_metadata") or {},
            is_active=True,
            created_by=principal.user_id,
            updated_by=principal.user_id,
        )
        await self.templates.add(tpl)
        await self.session.flush()
        return tpl

    async def apply_template(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        listing_id: uuid.UUID,
        template_id: uuid.UUID,
    ) -> ListingModel:
        await self._require_ws(principal, workspace_id)
        listing = await self.listings.get(workspace_id, listing_id)
        if listing is None:
            raise ListingNotFoundError()
        template = await self.templates.get(workspace_id, template_id)
        if template is None or not template.is_active:
            raise ListingTemplateNotFoundError()
        if template.title_template:
            listing.marketplace_title = template.title_template
            listing.internal_title = template.title_template
        if template.listing_format:
            listing.listing_format = template.listing_format
        if template.default_condition:
            listing.condition = template.default_condition
        if template.default_category_id:
            listing.category_id = template.default_category_id
        if template.marketplace_type:
            listing.marketplace_type = template.marketplace_type
        listing.template_id = template.id
        content = await self.content.get_by_listing(workspace_id, listing_id)
        if content is None:
            content = ListingContentModel(
                workspace_id=workspace_id,
                organization_id=listing.organization_id,
                listing_id=listing.id,
            )
            await self.content.add(content)
        if template.description_template:
            content.description = template.description_template
        if template.default_metadata:
            content.marketplace_metadata = {
                **(content.marketplace_metadata or {}),
                **template.default_metadata,
            }
        await self._record_version(listing, content, principal, reason="template_applied", changed_fields=["template"])
        await self.session.flush()
        return listing

    async def list_templates(self, principal: Principal, workspace_id: uuid.UUID) -> list[ListingTemplateModel]:
        await self._require_ws(principal, workspace_id, min_role=WorkspaceRole.READ_ONLY)
        return list(await self.templates.list(workspace_id))

    async def get_latest_validation(
        self, principal: Principal, workspace_id: uuid.UUID, listing_id: uuid.UUID
    ) -> tuple[ListingValidationResultModel | None, list]:
        await self.get(principal, workspace_id, listing_id)
        result = await self.validations.latest_for_listing(workspace_id, listing_id)
        if result is None:
            return None, []
        issues = list(await self.validations.list_issues(result.id))
        return result, issues
