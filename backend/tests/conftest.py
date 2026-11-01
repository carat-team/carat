import os
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, make_url, text

from carat_backend.rest.app import create_app
from carat_backend.settings import (
    DatabaseSettings,
    ObjectStorageSettings,
    PhotoSettings,
    Settings,
)

BACKEND_DIR = Path(__file__).parent.parent
TEST_BUCKET = "carat-test-photos"


@pytest.fixture(scope="session")
def database_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not set; start the services with `just backend test-services`")
    # The migration under test builds the schema, so a broken migration fails every API test
    config = Config(BACKEND_DIR / "alembic.ini")
    config.set_main_option("sqlalchemy.url", url)
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    return url


@pytest.fixture(scope="session")
def object_storage_url() -> str:
    url = os.environ.get("TEST_OBJECT_STORAGE_URL")
    if not url:
        pytest.skip("TEST_OBJECT_STORAGE_URL is not set; start the services with `just backend test-services`")
    return url


@pytest.fixture
def client(database_url: str, object_storage_url: str) -> Iterator[TestClient]:
    with create_engine(database_url).begin() as connection:
        connection.execute(text("TRUNCATE products CASCADE"))
    database = make_url(database_url)
    storage = urlsplit(object_storage_url)
    settings = Settings(
        database=DatabaseSettings(
            host=database.host or "localhost",
            port=database.port or 5432,
            name=database.database or "",
            user=database.username or "",
            password=database.password or "",
        ),
        object_storage=ObjectStorageSettings(
            endpoint=storage.netloc.rpartition("@")[2],
            bucket=TEST_BUCKET,
            secure=storage.scheme == "https",
            access_key=storage.username or "",
            secret_key=storage.password or "",
        ),
        photos=PhotoSettings(max_size_mb=1),
    )
    with TestClient(create_app(settings)) as test_client:
        yield test_client
