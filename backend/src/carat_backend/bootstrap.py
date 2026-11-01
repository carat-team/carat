"""Composition root: builds the services once from settings.

Every API adapter (the REST app today, a gRPC server later) gets its services from build_services(),
so the adapters stay thin and share one behaviour.
"""

from dataclasses import dataclass

from carat_algorithms.core import get_checks

from carat_backend.services.checks import CheckRunner, CheckService
from carat_backend.services.photos import PhotoService
from carat_backend.services.products import ProductService
from carat_backend.settings import Settings
from carat_backend.storage.database import create_session_factory
from carat_backend.storage.object_store import create_photo_object_store


@dataclass(frozen=True)
class Services:
    products: ProductService
    photos: PhotoService
    checks: CheckService


def build_services(settings: Settings) -> Services:
    session_factory = create_session_factory(settings.database.url)
    store = create_photo_object_store(settings.object_storage)
    products = ProductService(session_factory)
    return Services(
        products=products,
        photos=PhotoService(session_factory, store, settings.photos.max_size_mb * 1024 * 1024),
        checks=CheckService(products, store, CheckRunner(get_checks(), settings.checks.concurrency)),
    )
