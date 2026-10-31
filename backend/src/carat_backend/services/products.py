import uuid
from typing import Any

from carat_backend.domain.errors import NotFoundError
from carat_backend.domain.models import Product
from carat_backend.storage.database import SessionFactory
from carat_backend.storage.repositories.products import ProductRepository

# Perfumery only: the TN VED group is filled in automatically (CARAT_MVP, sheet 01)
DEFAULT_ATTRIBUTES: dict[str, Any] = {"tnVedCode": "3303"}


class ProductService:
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    def list(self) -> list[Product]:
        with self._session_factory.begin() as session:
            return ProductRepository(session).list()

    def get(self, product_id: uuid.UUID) -> Product:
        with self._session_factory.begin() as session:
            product = ProductRepository(session).get(product_id)
        if product is None:
            raise NotFoundError(f"Product {product_id} not found")
        return product

    def create(self, attributes: dict[str, Any]) -> Product:
        """Create a draft. Any attribute may be missing: the form decides what is required."""
        with self._session_factory.begin() as session:
            return ProductRepository(session).create({**DEFAULT_ATTRIBUTES, **attributes})

    def update(self, product_id: uuid.UUID, changes: dict[str, Any]) -> Product:
        """Merge changed attributes into the card; a None value removes the attribute."""
        with self._session_factory.begin() as session:
            product = ProductRepository(session).update_attributes(product_id, changes)
        if product is None:
            raise NotFoundError(f"Product {product_id} not found")
        return product
