import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from carat_backend.domain.models import Photo, Product, ProductStatus
from carat_backend.storage.tables import PhotoRow, ProductAttributeRow, ProductRow


class ProductRepository:
    """Products with their attributes and photo metadata. Returns domain models, never ORM rows."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list(self) -> list[Product]:
        rows = self._session.scalars(select(ProductRow).order_by(ProductRow.created_at.desc()))
        return [_product(row) for row in rows]

    def get(self, product_id: uuid.UUID) -> Product | None:
        row = self._session.get(ProductRow, product_id)
        return _product(row) if row else None

    def create(self, attributes: dict[str, Any]) -> Product:
        row = ProductRow(
            attributes=[ProductAttributeRow(attribute_key=key, value_json=value) for key, value in attributes.items()],
            photos=[],
        )
        self._session.add(row)
        self._session.flush()
        self._session.refresh(row)
        return _product(row)

    def update_attributes(self, product_id: uuid.UUID, changes: dict[str, Any]) -> Product | None:
        """Set every changed attribute; a None value removes the attribute."""
        row = self._session.get(ProductRow, product_id)
        if row is None:
            return None
        current = {attribute.attribute_key: attribute for attribute in row.attributes}
        for key, value in changes.items():
            if value is None:
                if key in current:
                    row.attributes.remove(current[key])
            elif key in current:
                current[key].value_json = value
            else:
                row.attributes.append(ProductAttributeRow(attribute_key=key, value_json=value))
        return self._touch(row)

    def add_photo(self, photo: Photo) -> Photo | None:
        row = self._session.get(ProductRow, photo.product_id)
        if row is None:
            return None
        row.photos.append(
            PhotoRow(
                id=photo.id,
                perspective=photo.perspective,
                package_id=photo.package_id,
                content_type=photo.content_type,
                size_bytes=photo.size_bytes,
                object_key=photo.object_key,
            )
        )
        self._touch(row)
        return photo

    def get_photo(self, product_id: uuid.UUID, photo_id: uuid.UUID) -> Photo | None:
        row = self._session.get(PhotoRow, photo_id)
        return _photo(row) if row and row.product_id == product_id else None

    def delete_photo(self, product_id: uuid.UUID, photo_id: uuid.UUID) -> Photo | None:
        row = self._session.get(PhotoRow, photo_id)
        if row is None or row.product_id != product_id:
            return None
        photo = _photo(row)
        self._session.delete(row)
        product = self._session.get(ProductRow, product_id)
        if product is not None:
            self._touch(product)
        return photo

    def _touch(self, row: ProductRow) -> Product:
        # Attribute and photo rows change without touching the products row, so bump updated_at by hand
        row.updated_at = func.now()  # pyright: ignore[reportAttributeAccessIssue]
        self._session.flush()
        self._session.refresh(row)
        return _product(row)


def _product(row: ProductRow) -> Product:
    return Product(
        id=row.id,
        status=ProductStatus(row.status),
        created_at=row.created_at,
        updated_at=row.updated_at,
        attributes={attribute.attribute_key: attribute.value_json for attribute in row.attributes},
        photos=tuple(_photo(photo) for photo in row.photos),
    )


def _photo(row: PhotoRow) -> Photo:
    return Photo(
        id=row.id,
        product_id=row.product_id,
        perspective=row.perspective,
        package_id=row.package_id,
        content_type=row.content_type,
        size_bytes=row.size_bytes,
        object_key=row.object_key,
    )
