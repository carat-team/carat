import logging
import threading
import time
from collections.abc import Sequence

from carat_algorithms.core import Check, CheckResult, CheckStatus, ProductCard

logger = logging.getLogger(__name__)

CHECK_CRASHED = "CHECK_CRASHED"


class CheckRunner:
    """Runs every check on a card. A crashing check becomes an ERROR result, never a failed request."""

    def __init__(self, checks: Sequence[Check], concurrency: int) -> None:
        self._checks = checks
        # ponytail: one semaphore around the whole run; add a per-check heavy flag if text checks start queueing
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
