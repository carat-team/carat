import uuid
from typing import Annotated

from fastapi import APIRouter, Form, Response, UploadFile

from carat_backend.rest.dependencies import ServicesDependency
from carat_backend.rest.schemas.photos import PhotoOut

router = APIRouter(prefix="/api/products/{product_id}/photos", tags=["photos"])


@router.post("", status_code=201)
def upload_photo(
    product_id: uuid.UUID,
    file: UploadFile,
    perspective: Annotated[str, Form(max_length=64)],
    services: ServicesDependency,
    package_id: Annotated[str | None, Form(alias="packageId", max_length=64)] = None,
) -> PhotoOut:
    # One byte past the limit is enough to reject an oversize upload without reading all of it
    content = file.file.read(services.photos.max_size_bytes + 1)
    return PhotoOut.from_domain(services.photos.add(product_id, content, file.content_type, perspective, package_id))


@router.get("/{photo_id}/content")
def get_photo_content(product_id: uuid.UUID, photo_id: uuid.UUID, services: ServicesDependency) -> Response:
    photo, content = services.photos.get_content(product_id, photo_id)
    return Response(content=content, media_type=photo.content_type)


@router.delete("/{photo_id}", status_code=204)
def delete_photo(product_id: uuid.UUID, photo_id: uuid.UUID, services: ServicesDependency) -> Response:
    services.photos.delete(product_id, photo_id)
    return Response(status_code=204)
