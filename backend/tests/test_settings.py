from pathlib import Path

import pytest

from carat_backend.settings import load_settings

BACKEND_DIR = Path(__file__).parent.parent


def test_committed_settings_file_loads() -> None:
    settings = load_settings(BACKEND_DIR / "settings.toml")

    assert settings.object_storage.bucket == "carat-photos"
    assert settings.weights.easyocr_dir == BACKEND_DIR / "../weights/easyocr"


def test_relative_weight_paths_resolve_against_the_file(tmp_path: Path) -> None:
    settings_file = tmp_path / "settings.toml"
    settings_file.write_text('[weights]\neasyocr_dir = "models/easyocr"\n[checks]\nconcurrency = 4\n')

    settings = load_settings(settings_file)

    assert settings.weights.easyocr_dir == tmp_path / "models/easyocr"
    assert settings.checks.concurrency == 4


def test_database_and_credentials_come_from_the_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DB_HOST", "db")
    monkeypatch.setenv("DB_PASSWORD", "secret")
    monkeypatch.setenv("S3_ACCESS_KEY", "key")
    settings_file = tmp_path / "settings.toml"
    settings_file.write_text("")

    settings = load_settings(settings_file)

    assert settings.database.url.host == "db"
    assert settings.database.url.password == "secret"
    assert settings.object_storage_credentials.access_key == "key"
