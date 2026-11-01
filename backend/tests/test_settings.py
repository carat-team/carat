from pathlib import Path

import pytest

from carat_backend.settings import load_settings

BACKEND_DIR = Path(__file__).parent.parent


def test_committed_settings_file_loads() -> None:
    settings = load_settings(BACKEND_DIR / "settings.toml")

    assert settings.weights.dir == BACKEND_DIR / "../weights"


def test_relative_weights_dir_resolves_against_the_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("WEIGHTS_DIR", "models")
    settings_file = tmp_path / "settings.toml"
    settings_file.write_text("[checks]\nconcurrency = 4\n")

    settings = load_settings(settings_file)

    assert settings.weights.dir == tmp_path / "models"
    assert settings.checks.concurrency == 4


def test_absolute_weights_dir_is_kept(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("WEIGHTS_DIR", "/app/weights")
    settings_file = tmp_path / "settings.toml"
    settings_file.write_text("")

    assert load_settings(settings_file).weights.dir == Path("/app/weights")


def test_database_and_object_storage_come_from_the_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DB_HOST", "db")
    monkeypatch.setenv("DB_PASSWORD", "secret")
    monkeypatch.setenv("S3_ENDPOINT", "s3:9000")
    monkeypatch.setenv("S3_SECURE", "true")
    monkeypatch.setenv("S3_ACCESS_KEY", "key")
    settings_file = tmp_path / "settings.toml"
    settings_file.write_text("")

    settings = load_settings(settings_file)

    assert settings.database.url.host == "db"
    assert settings.database.url.password == "secret"
    assert settings.object_storage.endpoint == "s3:9000"
    assert settings.object_storage.secure is True
    assert settings.object_storage.bucket == "carat-photos"
    assert settings.object_storage.access_key == "key"
