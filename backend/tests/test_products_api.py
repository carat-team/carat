import uuid
from typing import Any

from fastapi.testclient import TestClient

ATTRIBUTES: dict[str, Any] = {
    "fullName": "Духи тестовые 50 мл",
    "tnVedCode10": "3303001000",
    "gtin": "04748756756746",
    "brand": "шиккомпот",
    "country": ["RU"],
    "perfumeryType": "ДУХИ",
    "volume": {"value": 50, "unit": "мл"},
    "packageType": "ФЛАКОН",
    "packMaterial": "СТЕКЛО",
    "standardNumber": ["ТР ТС 009/2011"],
}


def create(client: TestClient, attributes: dict[str, Any] | None = None) -> dict[str, Any]:
    response = client.post("/api/products", json={"attributes": attributes or {}})
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


def test_create_without_body_makes_an_empty_draft(client: TestClient) -> None:
    response = client.post("/api/products")

    assert response.status_code == 201
    product = response.json()
    assert uuid.UUID(product["id"])
    assert product["status"] == "draft"
    assert product["attributes"] == {"tnVedCode": "3303"}
    assert product["photos"] == []


def test_create_stores_every_mvp_attribute(client: TestClient) -> None:
    product = create(client, ATTRIBUTES)

    assert product["attributes"] == {**ATTRIBUTES, "tnVedCode": "3303"}
    assert client.get(f"/api/products/{product['id']}").json() == product


def test_patch_merges_and_null_removes(client: TestClient) -> None:
    product = create(client, ATTRIBUTES)

    response = client.patch(
        f"/api/products/{product['id']}", json={"attributes": {"brand": "Example", "packageType": None}}
    )

    assert response.status_code == 200
    attributes = response.json()["attributes"]
    assert attributes["brand"] == "Example"
    assert "packageType" not in attributes
    assert attributes["gtin"] == ATTRIBUTES["gtin"]
    assert response.json()["updatedAt"] > product["updatedAt"]


def test_list_returns_catalog_rows_newest_first(client: TestClient) -> None:
    first = create(client, ATTRIBUTES)
    second = create(client)

    rows = client.get("/api/products").json()

    assert [row["id"] for row in rows] == [second["id"], first["id"]]
    assert rows[1] == {
        "id": first["id"],
        "name": ATTRIBUTES["fullName"],
        "status": "draft",
        "gtin": ATTRIBUTES["gtin"],
        "brand": ATTRIBUTES["brand"],
        "createdAt": first["createdAt"],
        "photoUrl": None,
    }


def test_format_errors_are_reported_by_field_path(client: TestClient) -> None:
    response = client.post(
        "/api/products",
        json={
            "attributes": {
                "fullName": "x" * 251,
                "tnVedCode10": "3303",
                "country": ["Russia"],
                "volume": {"value": -5, "unit": "кг"},
                "colour": "red",
            }
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "error": "VALIDATION_ERROR",
        "fields": {
            "fullName": "Слишком длинное значение",
            "tnVedCode10": "Неверный формат",
            "country.0": "Неверный формат",
            "volume.value": "Значение должно быть положительным числом",
            "volume.unit": "Недопустимое значение",
            "colour": "Неизвестное поле",
        },
    }


def test_wrong_type_has_a_message(client: TestClient) -> None:
    response = client.post("/api/products", json={"attributes": {"volume": {"value": "много", "unit": "мл"}}})

    assert response.json()["fields"] == {"volume.value": "Неверный тип значения"}


def test_patch_requires_the_attributes_object(client: TestClient) -> None:
    product = create(client)

    response = client.patch(f"/api/products/{product['id']}", json={})

    assert response.status_code == 422
    assert response.json()["fields"] == {"attributes": "Обязательное поле"}


def test_unknown_product_returns_404(client: TestClient) -> None:
    missing = uuid.uuid4()

    assert client.get(f"/api/products/{missing}").status_code == 404
    assert client.patch(f"/api/products/{missing}", json={"attributes": {}}).status_code == 404
