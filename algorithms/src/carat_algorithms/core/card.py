"""Product card as the checks see it. Field names follow docs/api.md (camelCase on the wire)."""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CardModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, frozen=True)


class Volume(CardModel):
    value: float
    unit: str


class CardPhoto(CardModel):
    content: bytes
    perspective: str | None = None
    package_id: str | None = None


class ProductCard(CardModel):
    """A field set to None is absent from the card, which is not the same as an empty value."""

    full_name: str | None = None
    tn_ved_code: str | None = None
    tn_ved_code10: str | None = None
    gtin: str | None = None
    brand: str | None = None
    country: list[str] | None = None
    perfumery_type: str | None = None
    volume: Volume | None = None
    package_type: str | None = None
    pack_material: str | None = None
    standard_number: list[str] | None = None
    photos: tuple[CardPhoto, ...] = ()
