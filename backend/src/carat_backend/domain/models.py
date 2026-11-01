import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any


class ProductStatus(StrEnum):
    DRAFT = "draft"
    ON_MODERATION = "on_moderation"
    PUBLISHED = "published"
    REJECTED = "rejected"


@dataclass(frozen=True)
class Photo:
    id: uuid.UUID
    product_id: uuid.UUID
    perspective: str
    package_id: str | None
    content_type: str
    size_bytes: int
    object_key: str


@dataclass(frozen=True)
class Product:
    id: uuid.UUID
    status: ProductStatus
    created_at: datetime
    updated_at: datetime
    # Card fields keyed by their API names (fullName, volume, ...), values as stored JSON
    attributes: dict[str, Any]
    photos: tuple[Photo, ...]
