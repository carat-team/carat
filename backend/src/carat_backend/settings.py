"""Backend settings.

Non-secret settings live in a TOML file (backend/settings.toml, or the file named by SETTINGS_FILE).
The database and object storage connections come from environment variables (.env).
"""

import os
import tomllib
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

DEFAULT_SETTINGS_FILE = Path("settings.toml")


class DatabaseSettings(BaseSettings):
    """DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD."""

    model_config = SettingsConfigDict(env_prefix="DB_")

    host: str = "localhost"
    port: int = 5432
    name: str = "carat"
    user: str = "carat"
    password: str = ""

    @property
    def url(self) -> URL:
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.name,
        )


class ObjectStorageSettings(BaseSettings):
    """S3_ENDPOINT (host:port), S3_BUCKET, S3_SECURE, S3_ACCESS_KEY, S3_SECRET_KEY."""

    model_config = SettingsConfigDict(env_prefix="S3_")

    endpoint: str = "localhost:9000"
    bucket: str = "carat-photos"
    secure: bool = False
    access_key: str = ""
    secret_key: str = ""


class PhotoSettings(BaseModel):
    max_size_mb: int = 10


class WeightsSettings(BaseSettings):
    """WEIGHTS_DIR: the repository's weights/ directory; each model family picks its own subdirectory."""

    model_config = SettingsConfigDict(env_prefix="WEIGHTS_")

    dir: Path = Path("../weights")


class CheckSettings(BaseModel):
    # How many cards may run checks at the same time; heavy checks share one process
    concurrency: int = 2


class Settings(BaseModel):
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    object_storage: ObjectStorageSettings = Field(default_factory=ObjectStorageSettings)
    photos: PhotoSettings = PhotoSettings()
    weights: WeightsSettings = Field(default_factory=WeightsSettings)
    checks: CheckSettings = CheckSettings()


def load_settings(path: Path) -> Settings:
    """Read a settings TOML file. A relative WEIGHTS_DIR resolves against the file's directory."""
    settings = Settings.model_validate(tomllib.loads(path.read_text()))
    if settings.weights.dir.is_absolute():
        return settings
    weights = settings.weights.model_copy(update={"dir": path.parent / settings.weights.dir})
    return settings.model_copy(update={"weights": weights})


@lru_cache
def get_settings() -> Settings:
    return load_settings(Path(os.environ.get("SETTINGS_FILE", DEFAULT_SETTINGS_FILE)))
