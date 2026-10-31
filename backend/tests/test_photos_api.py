import uuid

import httpx2
from fastapi.testclient import TestClient

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


def create_product(client: TestClient) -> str:
    product_id: str = client.post("/api/products").json()["id"]
    return product_id


def upload(
    client: TestClient, product_id: str, content: bytes = PNG, content_type: str = "image/png"
) -> httpx2.Response:
    return client.post(
        f"/api/products/{product_id}/photos",
        files={"file": ("../../evil name.png", content, content_type)},
        data={"perspective": "front", "packageId": "main"},
    )


def test_upload_returns_url_that_serves_the_same_bytes(client: TestClient) -> None:
    product_id = create_product(client)

    response = upload(client, product_id)

    assert response.status_code == 201, response.text
    photo = response.json()
    assert photo["url"] == f"/api/products/{product_id}/photos/{photo['id']}/content"
    assert (photo["perspective"], photo["packageId"]) == ("front", "main")
    content = client.get(photo["url"])
    assert content.status_code == 200
    assert content.content == PNG
    assert content.headers["content-type"] == "image/png"
    assert client.get(f"/api/products/{product_id}").json()["photos"] == [photo]
    assert client.get("/api/products").json()[0]["photoUrl"] == photo["url"]


def test_wrong_type_empty_and_oversize_files_are_rejected(client: TestClient) -> None:
    product_id = create_product(client)

    responses = [
        upload(client, product_id, b"<html></html>", "text/html"),
        upload(client, product_id, b""),
        upload(client, product_id, b"\x00" * (1024 * 1024 + 1)),
    ]

    assert [response.status_code for response in responses] == [422, 422, 422]
    assert all(list(response.json()["fields"]) == ["file"] for response in responses)
    assert client.get(f"/api/products/{product_id}").json()["photos"] == []


def test_missing_perspective_is_a_validation_error(client: TestClient) -> None:
    response = client.post(
        f"/api/products/{create_product(client)}/photos", files={"file": ("photo.png", PNG, "image/png")}
    )

    assert response.status_code == 422
    assert response.json()["fields"] == {"perspective": "Обязательное поле"}


def test_delete_removes_photo_and_its_content(client: TestClient) -> None:
    product_id = create_product(client)
    photo = upload(client, product_id).json()

    response = client.delete(f"/api/products/{product_id}/photos/{photo['id']}")

    assert response.status_code == 204
    assert client.get(f"/api/products/{product_id}").json()["photos"] == []
    assert client.get(photo["url"]).status_code == 404


def test_unknown_product_or_photo_returns_404(client: TestClient) -> None:
    product_id = create_product(client)

    assert upload(client, str(uuid.uuid4())).status_code == 404
    assert client.get(f"/api/products/{product_id}/photos/{uuid.uuid4()}/content").status_code == 404
    assert client.delete(f"/api/products/{product_id}/photos/{uuid.uuid4()}").status_code == 404
