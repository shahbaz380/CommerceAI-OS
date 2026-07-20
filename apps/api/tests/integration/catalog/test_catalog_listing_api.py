"""Catalog + listing API integration tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta


def _auth(client, email: str) -> dict[str, str]:
    r = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Str0ng!Passw0rd"},
    )
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _workspace(client, headers: dict[str, str], slug: str) -> str:
    org = client.post(
        "/api/v1/organizations",
        headers=headers,
        json={"name": f"Org {slug}", "slug": slug},
    )
    assert org.status_code == 201, org.text
    wss = client.get(f"/api/v1/organizations/{org.json()['id']}/workspaces", headers=headers)
    assert wss.status_code == 200
    return wss.json()[0]["id"]


def test_product_and_listing_lifecycle(client) -> None:
    headers = _auth(client, "catalog1@example.com")
    ws = _workspace(client, headers, "cat-ws-1")
    h = {**headers, "X-Workspace-Id": ws}

    # category
    cat = client.post(
        "/api/v1/product-categories",
        headers=h,
        json={"name": "Electronics", "slug": "electronics"},
    )
    assert cat.status_code == 201, cat.text
    cat_id = cat.json()["id"]

    # product
    prod = client.post(
        "/api/v1/products",
        headers=h,
        json={
            "name": "Wireless Mouse",
            "description": "Ergonomic mouse",
            "brand": "Acme",
            "default_sku": "mouse-001",
            "condition": "new",
        },
    )
    assert prod.status_code == 201, prod.text
    product_id = prod.json()["id"]
    assert prod.json()["default_sku"] == "MOUSE-001"
    assert prod.json()["status"] == "draft"

    # activate product
    act = client.post(f"/api/v1/products/{product_id}/activate", headers=h)
    assert act.status_code == 200
    assert act.json()["status"] == "active"

    # variant
    var = client.post(
        f"/api/v1/products/{product_id}/variants",
        headers=h,
        json={"sku": "mouse-001-blk", "title": "Black", "option_values": {"color": "black"}},
    )
    assert var.status_code == 201, var.text
    variant_id = var.json()["id"]

    # attribute definition
    attr_def = client.post(
        "/api/v1/product-attributes",
        headers=h,
        json={
            "code": "color",
            "name": "Color",
            "data_type": "text",
            "is_searchable": True,
        },
    )
    assert attr_def.status_code == 201, attr_def.text
    attr_def_id = attr_def.json()["id"]

    # product tags
    tags = client.post(
        f"/api/v1/products/{product_id}/tags",
        headers=h,
        json={"tags": ["wireless", "ergonomic", "wireless"]},
    )
    assert tags.status_code == 200, tags.text
    assert tags.json()["tags"] == ["wireless", "ergonomic"]

    # media
    media = client.post(
        f"/api/v1/products/{product_id}/media",
        headers=h,
        json={"url": "https://cdn.example.com/mouse.jpg", "is_primary": True, "mime_type": "image/jpeg"},
    )
    assert media.status_code == 201, media.text

    # attribute values
    attribute = client.post(
        f"/api/v1/products/{product_id}/attributes",
        headers=h,
        json={"attribute_definition_id": attr_def_id, "value_text": "black"},
    )
    assert attribute.status_code == 201, attribute.text

    # assign category
    asg = client.post(f"/api/v1/products/{product_id}/categories/{cat_id}", headers=h)
    assert asg.status_code == 201

    # listing draft
    listing = client.post(
        "/api/v1/listings",
        headers=h,
        json={
            "product_id": product_id,
            "product_variant_id": variant_id,
            "marketplace_type": "ebay",
            "marketplace_title": "Acme Wireless Mouse",
            "description": "A great wireless mouse for work",
            "price_amount": "29.99",
            "quantity": 5,
            "category_id": cat_id,
            "currency": "usd",
        },
    )
    assert listing.status_code == 201, listing.text
    listing_id = listing.json()["id"]
    assert listing.json()["status"] == "draft"
    assert listing.json()["currency"] == "USD"

    # validate
    val = client.post(f"/api/v1/listings/{listing_id}/validate", headers=h)
    assert val.status_code == 200, val.text
    assert val.json()["passed"] is True

    # submit + approve
    sub = client.post(f"/api/v1/listings/{listing_id}/submit-for-review", headers=h)
    assert sub.status_code == 200, sub.text
    assert sub.json()["status"] == "ready_for_review"

    appr = client.post(f"/api/v1/listings/{listing_id}/approve", headers=h)
    assert appr.status_code == 200, appr.text
    assert appr.json()["status"] == "approved"

    # schedule
    future = (datetime.now(UTC) + timedelta(days=2)).isoformat()
    sch = client.post(
        f"/api/v1/listings/{listing_id}/schedule",
        headers=h,
        json={"scheduled_publish_at": future},
    )
    assert sch.status_code == 200, sch.text
    assert sch.json()["status"] == "scheduled"

    # versions
    vers = client.get(f"/api/v1/listings/{listing_id}/versions", headers=h)
    assert vers.status_code == 200
    assert len(vers.json()) >= 1

    # template
    tpl = client.post(
        "/api/v1/listing-templates",
        headers=h,
        json={
            "name": "Default eBay",
            "marketplace_type": "ebay",
            "title_template": "Template Title {{name}}",
            "description_template": "Template body",
        },
    )
    assert tpl.status_code == 201, tpl.text

    # tenant isolation: other workspace cannot see product
    headers2 = _auth(client, "other@example.com")
    ws2 = _workspace(client, headers2, "cat-ws-other")
    denied = client.get(
        f"/api/v1/products/{product_id}",
        headers={**headers2, "X-Workspace-Id": ws2},
    )
    assert denied.status_code == 404


def test_duplicate_sku_conflict(client) -> None:
    headers = _auth(client, "sku@example.com")
    ws = _workspace(client, headers, "sku-ws")
    h = {**headers, "X-Workspace-Id": ws}
    r1 = client.post("/api/v1/products", headers=h, json={"name": "A", "default_sku": "SAME-SKU"})
    assert r1.status_code == 201
    r2 = client.post("/api/v1/products", headers=h, json={"name": "B", "default_sku": "same-sku"})
    assert r2.status_code == 409


def test_product_restore_after_archive(client) -> None:
    headers = _auth(client, "restore@example.com")
    ws = _workspace(client, headers, "restore-ws")
    h = {**headers, "X-Workspace-Id": ws}

    created = client.post("/api/v1/products", headers=h, json={"name": "Restore Me", "default_sku": "RESTORE-001"})
    assert created.status_code == 201, created.text
    product_id = created.json()["id"]

    archived = client.delete(f"/api/v1/products/{product_id}", headers=h)
    assert archived.status_code == 200, archived.text

    restored = client.post(f"/api/v1/products/{product_id}/restore", headers=h)
    assert restored.status_code == 200, restored.text
    assert restored.json()["status"] == "draft"


def test_invalid_listing_transition(client) -> None:
    headers = _auth(client, "life@example.com")
    ws = _workspace(client, headers, "life-ws")
    h = {**headers, "X-Workspace-Id": ws}
    p = client.post("/api/v1/products", headers=h, json={"name": "P", "auto_sku": True})
    listing = client.post(
        "/api/v1/listings",
        headers=h,
        json={
            "product_id": p.json()["id"],
            "description": "desc",
            "marketplace_title": "Title",
        },
    )
    listing_id = listing.json()["id"]
    # approve from draft should fail
    bad = client.post(f"/api/v1/listings/{listing_id}/approve", headers=h)
    assert bad.status_code in (400, 422)
