"""Product bodies. Field names, types and formats follow docs/api.md (CARAT_MVP, sheets 01 and 03)."""

import uuid
from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import Field, StringConstraints

from carat_backend.domain.models import Product, ProductStatus
from carat_backend.rest.schemas.common import ApiModel
from carat_backend.rest.schemas.photos import PhotoOut, photo_url

CountryCode = Annotated[str, StringConstraints(pattern=r"^[A-Z]{2}$")]


class Volume(ApiModel):
    value: float = Field(gt=0)
    unit: Literal["л", "мл", "г"]


class ProductAttributes(ApiModel):
    """Format checks only: any field may be missing in a draft, dictionary values are not restricted."""

    full_name: str | None = Field(default=None, max_length=250)
    tn_ved_code: str | None = None
    tn_ved_code10: str | None = Field(default=None, pattern=r"^\d{10}$")
    gtin: str | None = None
    brand: str | None = None
    country: list[CountryCode] | None = None
    perfumery_type: str | None = None
    volume: Volume | None = None
    package_type: str | None = None
    pack_material: str | None = None
    standard_number: list[str] | None = None


class ProductCreate(ApiModel):
    attributes: ProductAttributes = Field(default_factory=ProductAttributes)


class ProductUpdate(ApiModel):
    """Only the attributes present in the request change; null removes an attribute."""

    attributes: ProductAttributes


class ProductOut(ApiModel):
    id: uuid.UUID
    status: ProductStatus
    created_at: datetime
    updated_at: datetime
    attributes: dict[str, Any]
    photos: list[PhotoOut]

    @classmethod
    def from_domain(cls, product: Product) -> "ProductOut":
        return cls(
            id=product.id,
            status=product.status,
            created_at=product.created_at,
            updated_at=product.updated_at,
            attributes=product.attributes,
            photos=[PhotoOut.from_domain(photo) for photo in product.photos],
        )


class ProductListItem(ApiModel):
    """One catalog row: the MVP fields (id, name, status) plus what the catalog table shows."""

    id: uuid.UUID
    name: str | None
    status: ProductStatus
    gtin: str | None
    brand: str | None
    created_at: datetime
    photo_url: str | None

    @classmethod
    def from_domain(cls, product: Product) -> "ProductListItem":
        return cls(
            id=product.id,
            name=product.attributes.get("fullName"),
            status=product.status,
            gtin=product.attributes.get("gtin"),
            brand=product.attributes.get("brand"),
            created_at=product.created_at,
            photo_url=photo_url(product.photos[0]) if product.photos else None,
        )
