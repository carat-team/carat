import uuid

from carat_backend.domain.models import Photo
from carat_backend.rest.schemas.common import ApiModel


def photo_url(photo: Photo) -> str:
    return f"/api/products/{photo.product_id}/photos/{photo.id}/content"


class PhotoOut(ApiModel):
    id: uuid.UUID
    url: str
    perspective: str
    package_id: str | None

    @classmethod
    def from_domain(cls, photo: Photo) -> "PhotoOut":
        return cls(id=photo.id, url=photo_url(photo), perspective=photo.perspective, package_id=photo.package_id)
