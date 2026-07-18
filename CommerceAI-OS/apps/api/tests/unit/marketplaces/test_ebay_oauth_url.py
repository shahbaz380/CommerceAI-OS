"""eBay OAuth URL builder tests."""

from app.infrastructure.marketplace.ebay.oauth.client import EbayOAuthClient, EbayOAuthConfig


def test_build_authorization_url_sandbox() -> None:
    client = EbayOAuthClient(
        EbayOAuthConfig(
            client_id="client-id",
            client_secret="secret",
            redirect_uri="https://app.example.com/callback",
            environment="sandbox",
            scopes="scope1 scope2",
        )
    )
    url = client.build_authorization_url(state="abc123")
    assert "auth.sandbox.ebay.com" in url
    assert "client_id=client-id" in url
    assert "state=abc123" in url
    assert "response_type=code" in url
