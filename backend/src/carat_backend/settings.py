"""Backend settings.

Non-secret settings live in a TOML file (backend/settings.toml, or the file named by SETTINGS_FILE).
The database connection and object storage credentials come from environment variables (.env).
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


class ObjectStorageCredentials(BaseSettings):
    """S3_ACCESS_KEY, S3_SECRET_KEY."""

    model_config = SettingsConfigDict(env_prefix="S3_")

    access_key: str = ""
    secret_key: str = ""


class ObjectStorageSettings(BaseModel):
    endpoint: str = "localhost:9000"
    bucket: str = "carat-photos"
    secure: bool = False


class PhotoSettings(BaseModel):
    max_size_mb: int = 10


class WeightsSettings(BaseModel):
    """One directory per model family under the repository's weights/ directory."""

    easyocr_dir: Path = Path("../weights/easyocr")


class CheckSettings(BaseModel):
    # How many cards may run checks at the same time; heavy checks share one process
    concurrency: int = 2


class Settings(BaseModel):
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    object_storage: ObjectStorageSettings = ObjectStorageSettings()
    object_storage_credentials: ObjectStorageCredentials = Field(default_factory=ObjectStorageCredentials)
    photos: PhotoSettings = PhotoSettings()
    weights: WeightsSettings = WeightsSettings()
    checks: CheckSettings = CheckSettings()


def load_settings(path: Path) -> Settings:
    """Read a settings TOML file. Relative weight paths resolve against the file's directory."""
    settings = Settings.model_validate(tomllib.loads(path.read_text()))
    resolved = {
        name: path.parent / value
        for name, value in settings.weights.model_dump().items()
        if isinstance(value, Path) and not value.is_absolute()
    }
    return settings.model_copy(update={"weights": settings.weights.model_copy(update=resolved)})


@lru_cache
def get_settings() -> Settings:
    return load_settings(Path(os.environ.get("SETTINGS_FILE", DEFAULT_SETTINGS_FILE)))
