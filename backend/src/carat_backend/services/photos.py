import uuid

from carat_backend.domain.errors import InvalidInputError, NotFoundError
from carat_backend.domain.models import Photo
from carat_backend.storage.database import SessionFactory
from carat_backend.storage.object_store import PhotoObjectStore
from carat_backend.storage.repositories.products import ProductRepository

EXTENSIONS = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


class PhotoService:
    def __init__(self, session_factory: SessionFactory, store: PhotoObjectStore, max_size_bytes: int) -> None:
        self._session_factory = session_factory
        self._store = store
        self.max_size_bytes = max_size_bytes

    def add(
        self,
        product_id: uuid.UUID,
        content: bytes,
        content_type: str | None,
        perspective: str,
        package_id: str | None,
    ) -> Photo:
        extension = EXTENSIONS.get(content_type or "")
        if content_type is None or extension is None:
            raise InvalidInputError({"file": "Допустимы только фото в формате JPEG, PNG или WEBP"})
        if not content:
            raise InvalidInputError({"file": "Файл пустой"})
        if len(content) > self.max_size_bytes:
            raise InvalidInputError({"file": f"Файл больше {self.max_size_bytes // (1024 * 1024)} МБ"})

        photo_id = uuid.uuid4()
        photo = Photo(
            id=photo_id,
            product_id=product_id,
            perspective=perspective,
            package_id=package_id,
            content_type=content_type,
            size_bytes=len(content),
            # The client's file name is never used
            object_key=f"products/{product_id}/{photo_id}.{extension}",
        )
        with self._session_factory.begin() as session:
            if ProductRepository(session).get(product_id) is None:
                raise NotFoundError(f"Product {product_id} not found")

        self._store.put(photo.object_key, content, content_type)
        try:
            with self._session_factory.begin() as session:
                saved = ProductRepository(session).add_photo(photo)
        except Exception:
            # The row was not committed, so the object must not stay behind
            self._store.delete(photo.object_key)
            raise
        if saved is None:
            # The product was deleted while the photo was uploading
            self._store.delete(photo.object_key)
            raise NotFoundError(f"Product {product_id} not found")
        return saved

    def get_content(self, product_id: uuid.UUID, photo_id: uuid.UUID) -> tuple[Photo, bytes]:
        with self._session_factory.begin() as session:
            photo = ProductRepository(session).get_photo(product_id, photo_id)
        if photo is None:
            raise NotFoundError(f"Photo {photo_id} not found")
        return photo, self._store.get(photo.object_key)

    def delete(self, product_id: uuid.UUID, photo_id: uuid.UUID) -> None:
        with self._session_factory.begin() as session:
            photo = ProductRepository(session).delete_photo(product_id, photo_id)
        if photo is None:
            raise NotFoundError(f"Photo {photo_id} not found")
        # After the commit: a failed delete leaves an orphan object, never a row without its image
        self._store.delete(photo.object_key)
