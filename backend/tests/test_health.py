import logging
import threading
import time
from collections.abc import Mapping
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from carat_backend.domain.health import ComponentStatus
from carat_backend.main import create_app
from carat_backend.services.health import PROBE_FAILED, PROBE_TIMEOUT, HealthService, Probe
from carat_backend.settings import DatabaseSettings, HealthSettings, ObjectStorageSettings, Settings


class FakeProbe:
    def __init__(self, error: Exception | None = None, delay: float = 0.0) -> None:
        self._error = error
        self._delay = delay

    def check(self) -> None:
        if self._delay:
            threading.Event().wait(self._delay)
        if self._error is not None:
            raise self._error


def client_with_probes(probes: Mapping[str, Probe]) -> TestClient:
    app = create_app()
    app.state.services = replace(app.state.services, health=HealthService(probes, timeout_seconds=1))
    return TestClient(app)


def test_health_returns_ok() -> None:
    response = TestClient(create_app()).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_service_reports_every_probe_up() -> None:
    report = HealthService({"database": FakeProbe(), "object_storage": FakeProbe()}, timeout_seconds=1).check()

    assert report.ready
    assert [component.name for component in report.components] == ["database", "object_storage"]
    assert all(c.status is ComponentStatus.UP and c.reason_code is None for c in report.components)


def test_service_marks_a_failed_probe_down_without_leaking_the_error(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.WARNING)
    probes = {"database": FakeProbe(), "object_storage": FakeProbe(error=RuntimeError("password=secret-value"))}

    report = HealthService(probes, timeout_seconds=1).check()

    components = {component.name: component for component in report.components}
    assert not report.ready
    assert components["database"].status is ComponentStatus.UP
    assert components["object_storage"].status is ComponentStatus.DOWN
    assert components["object_storage"].reason_code == PROBE_FAILED
    assert "RuntimeError" in caplog.text
    assert "secret-value" not in caplog.text


def test_service_marks_a_slow_probe_down_within_the_limit() -> None:
    service = HealthService({"database": FakeProbe(), "object_storage": FakeProbe(delay=2)}, timeout_seconds=0.3)

    started = time.monotonic()
    report = service.check()

    components = {component.name: component for component in report.components}
    assert time.monotonic() - started < 1
    assert components["database"].status is ComponentStatus.UP
    assert components["object_storage"].status is ComponentStatus.DOWN
    assert components["object_storage"].reason_code == PROBE_TIMEOUT


def test_service_keeps_healthy_probes_up_while_another_one_hangs() -> None:
    service = HealthService({"database": FakeProbe(), "object_storage": FakeProbe(delay=1)}, timeout_seconds=0.1)

    reports = [service.check() for _ in range(8)]

    for report in reports:
        components = {component.name: component for component in report.components}
        assert components["database"].status is ComponentStatus.UP
        assert components["object_storage"].status is ComponentStatus.DOWN


def test_ready_returns_ok_when_every_dependency_works() -> None:
    response = client_with_probes({"database": FakeProbe(), "object_storage": FakeProbe()}).get("/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["components"]["database"]["status"] == "up"
    assert body["components"]["object_storage"]["status"] == "up"


def test_ready_returns_503_when_the_object_storage_is_down() -> None:
    probes = {"database": FakeProbe(), "object_storage": FakeProbe(error=ConnectionError("s3 is gone"))}

    response = client_with_probes(probes).get("/health/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "unavailable"
    assert body["components"]["database"]["status"] == "up"
    assert body["components"]["object_storage"]["status"] == "down"
    assert body["components"]["object_storage"]["reason_code"] == PROBE_FAILED


def test_ready_returns_503_for_unreachable_services() -> None:
    # Port 1 refuses connections at once, so the real probes fail fast without any running service
    settings = Settings(
        database=DatabaseSettings(host="127.0.0.1", port=1, name="carat", user="carat", password="unused"),
        object_storage=ObjectStorageSettings(endpoint="127.0.0.1:1", access_key="unused", secret_key="unused"),
        health=HealthSettings(timeout_seconds=2),
    )

    response = TestClient(create_app(settings)).get("/health/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "unavailable"
    assert {name: component["status"] for name, component in body["components"].items()} == {
        "database": "down",
        "object_storage": "down",
    }


def test_ready_returns_ok_with_real_services(client: TestClient) -> None:
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
