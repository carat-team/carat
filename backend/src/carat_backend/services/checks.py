import logging
import threading
import time
import uuid
from collections.abc import Sequence

from carat_algorithms.core import CardPhoto, Check, CheckResult, CheckStatus, ProductCard

from carat_backend.services.products import ProductService
from carat_backend.storage.object_store import PhotoObjectStore

logger = logging.getLogger(__name__)

CHECK_CRASHED = "CHECK_CRASHED"


class CheckRunner:
    """Runs every check on a card. A crashing check becomes an ERROR result, never a failed request."""

    def __init__(self, checks: Sequence[Check], concurrency: int) -> None:
        self._checks = checks
        self._semaphore = threading.BoundedSemaphore(concurrency)

    def run(self, card: ProductCard) -> list[CheckResult]:
        with self._semaphore:
            return [self._run_one(check, card) for check in self._checks]

    def _run_one(self, check: Check, card: ProductCard) -> CheckResult:
        started = time.perf_counter()
        try:
            result = check.run(card)
        except Exception:
            # The traceback may quote card values, so only the check id is logged
            logger.error("Check crashed: check_id=%s", check.check_id)
            result = CheckResult(
                check_id=check.check_id,
                status=CheckStatus.ERROR,
                reason_code=CHECK_CRASHED,
                explanation="Проверка завершилась с ошибкой",
                field_refs=(),
                algorithm_version=check.algorithm_version,
            )
        duration_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "Check finished: check_id=%s status=%s duration_ms=%.1f", check.check_id, result.status, duration_ms
        )
        return result


class CheckService:
    """Builds a ProductCard from a stored product and runs the checks on it."""

    def __init__(self, products: ProductService, store: PhotoObjectStore, runner: CheckRunner) -> None:
        self._products = products
        self._store = store
        self._runner = runner

    def check(self, product_id: uuid.UUID) -> list[CheckResult]:
        product = self._products.get(product_id)
        photos = tuple(
            CardPhoto(
                content=self._store.get(photo.object_key), perspective=photo.perspective, package_id=photo.package_id
            )
            for photo in product.photos
        )
        return self._runner.run(ProductCard.model_validate({**product.attributes, "photos": photos}))
