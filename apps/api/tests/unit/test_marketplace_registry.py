"""Marketplace registry placeholder tests."""

from __future__ import annotations

import pytest

from app.infrastructure.marketplace.registry import build_default_registry
from app.shared.exceptions import AppError


@pytest.mark.asyncio
async def test_ebay_registered() -> None:
    reg = build_default_registry()
    assert "ebay" in reg.list_channels()
    adapter = reg.get("ebay")
    assert adapter is not None
    health = await adapter.health()
    assert health["channel"] == "ebay"


@pytest.mark.asyncio
async def test_stateless_adapter_requires_factory() -> None:
    from uuid import uuid4

    from app.infrastructure.marketplace.base import MarketplaceContext

    reg = build_default_registry()
    adapter = reg.get("ebay")
    assert adapter is not None
    with pytest.raises(AppError):
        await adapter.begin_connect(MarketplaceContext(workspace_id=uuid4(), user_id=uuid4()))
