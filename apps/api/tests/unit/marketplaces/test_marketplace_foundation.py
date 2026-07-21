from __future__ import annotations

from app.application.marketplaces.provider_service import MarketplaceProviderResolver
from app.domain.marketplaces.enums import MarketplaceProvider


def test_provider_resolver_supports_ebay_oauth() -> None:
    resolver = MarketplaceProviderResolver()

    provider = resolver.resolve("ebay")

    assert provider is MarketplaceProvider.EBAY
    capabilities = resolver.capabilities(provider)
    assert any(cap.name == "oauth" and cap.supported for cap in capabilities)
    assert any(cap.name == "inventory" and cap.supported for cap in capabilities)
