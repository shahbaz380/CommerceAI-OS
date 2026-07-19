"""Exception taxonomy tests."""

from app.shared.exceptions import BusinessRuleError, MarketplaceError, ValidationAppError


def test_validation_error_payload() -> None:
    err = ValidationAppError("bad", details=[{"field": "x", "issue": "required"}])
    payload = err.to_dict()
    assert payload["code"] == "VALIDATION_ERROR"
    assert payload["details"][0]["field"] == "x"
    assert err.http_status == 400


def test_business_rule_status() -> None:
    err = BusinessRuleError("nope")
    assert err.http_status == 422


def test_marketplace_error_provider() -> None:
    err = MarketplaceError("down", provider="ebay", provider_code="RATE_LIMIT")
    assert err.provider == "ebay"
    assert any(d.get("field") == "providerCode" for d in err.details)
