import io
import uuid
from pathlib import Path

import httpx2
import numpy as np
import pytest
from carat_algorithms.vision.background.masks import Array
from carat_algorithms.vision.background.segmentation import ISNetSegmenter
from fastapi.testclient import TestClient
from PIL import Image


def encode_image(image_format: str) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (1, 1)).save(buffer, format=image_format)
    return buffer.getvalue()


PNG = encode_image("PNG")


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
        upload(client, product_id, b"\x89PNG\r\n\x1a\n" + b"\x00" * 64),
        upload(client, product_id, encode_image("JPEG")),
    ]

    assert [response.status_code for response in responses] == [422, 422, 422, 422, 422]
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


def test_cutout_returns_png_and_preserves_original(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    image = Image.new("RGB", (10, 10), "red")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    original = buffer.getvalue()
    product_id = create_product(client)
    photo = upload(client, product_id, original).json()
    content_url: str = photo["url"]
    cutout_url = content_url.removesuffix("/content") + "/cutout"

    mask = np.zeros((10, 10), dtype=np.uint8)
    mask[2:8, 4:6] = 255
    mask[2, 4] = 64

    def segment(_segmenter: ISNetSegmenter, _source: Image.Image) -> Array:
        return mask

    weights_dir = tmp_path / "weights"
    weights_file = ISNetSegmenter(weights_dir).weights_path
    weights_file.parent.mkdir(parents=True)
    monkeypatch.setattr(ISNetSegmenter, "segment", segment)
    assert client.post(cutout_url).status_code == 503
    weights_file.touch()
    response = client.post(cutout_url)
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "image/png"
    with Image.open(io.BytesIO(response.content)) as result:
        assert (result.format, result.mode, result.size) == ("PNG", "RGBA", (2, 6))
        assert result.getchannel("A").getextrema() == (64, 255)
    assert client.get(content_url).content == original
    assert client.post(cutout_url.replace(product_id, str(uuid.uuid4()))).status_code == 404
    mask.fill(0)
    no_product = client.post(cutout_url)
    assert no_product.status_code == 422
    assert no_product.json()["fields"] == {"photo": "На фото не удалось выделить товар"}
