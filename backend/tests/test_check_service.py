import threading
import uuid
from datetime import UTC, datetime

from carat_algorithms.core import CheckResult, CheckStatus, ProductCard

from carat_backend.domain.models import Photo, Product, ProductStatus
from carat_backend.services.checks import CheckRunner, CheckService
from carat_backend.services.products import ProductService
from carat_backend.storage.object_store import PhotoObjectStore

PRODUCT_ID = uuid.uuid4()


class FixedProducts(ProductService):
    def __init__(self) -> None:
        pass

    def get(self, product_id: uuid.UUID) -> Product:
        photo = Photo(
            id=uuid.uuid4(),
            product_id=product_id,
            perspective="front",
            package_id=None,
            content_type="image/png",
            size_bytes=4,
            object_key="photo.png",
        )
        now = datetime.now(UTC)
        return Product(
            id=product_id, status=ProductStatus.DRAFT, created_at=now, updated_at=now, attributes={}, photos=(photo,)
        )


class CountingStore(PhotoObjectStore):
    def __init__(self) -> None:
        self.loads = 0

    def get(self, key: str) -> bytes:
        self.loads += 1
        return b"data"


class BlockingCheck:
    check_id = "blocking"
    algorithm_version = 1

    def __init__(self) -> None:
        self.started = threading.Event()
        self.release = threading.Event()

    def run(self, card: ProductCard) -> CheckResult:
        self.started.set()
        self.release.wait(timeout=5)
        return CheckResult(
            check_id=self.check_id,
            status=CheckStatus.PASS,
            reason_code="BLOCKING_OK",
            explanation="Проверка пройдена",
            field_refs=(),
            algorithm_version=self.algorithm_version,
        )


def test_waiting_request_loads_no_photos_until_it_gets_a_slot() -> None:
    store = CountingStore()
    check = BlockingCheck()
    service = CheckService(FixedProducts(), store, CheckRunner([check]), concurrency=1)
    first = threading.Thread(target=service.check, args=(PRODUCT_ID,))
    second = threading.Thread(target=service.check, args=(PRODUCT_ID,))

    first.start()
    assert check.started.wait(timeout=5)
    second.start()
    second.join(timeout=0.2)

    assert store.loads == 1
    check.release.set()
    first.join(timeout=5)
    second.join(timeout=5)
    assert store.loads == 2
