import uuid

from carat_algorithms.core import get_checks
from fastapi.testclient import TestClient


def test_check_returns_one_result_per_registered_check(client: TestClient) -> None:
    product_id = client.post("/api/products", json={"attributes": {"gtin": "3614272049529"}}).json()["id"]

    response = client.post(f"/api/products/{product_id}/check")

    assert response.status_code == 200
    results = response.json()
    assert [result["check_id"] for result in results] == [check.check_id for check in get_checks()]
    assert set(results[0]) == {"check_id", "status", "reason_code", "explanation", "field_refs", "algorithm_version"}


def test_check_of_unknown_product_returns_404(client: TestClient) -> None:
    assert client.post(f"/api/products/{uuid.uuid4()}/check").status_code == 404
