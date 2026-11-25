import logging
import time
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from typing import Protocol

from carat_backend.domain.health import ComponentHealth, ComponentStatus, HealthReport

logger = logging.getLogger(__name__)

PROBE_FAILED = "PROBE_FAILED"
PROBE_TIMEOUT = "PROBE_TIMEOUT"


class Probe(Protocol):
    def check(self) -> None:
        """Return when the dependency works, raise when it does not."""


class HealthService:
    """Runs the dependency probes in parallel, each within the time limit, and reports which of them work."""

    def __init__(self, probes: Mapping[str, Probe], timeout_seconds: float) -> None:
        self._probes = dict(probes)
        self._timeout_seconds = timeout_seconds
        # One pool per probe: a probe that hangs can only occupy its own workers, never the others'
        self._executors = {
            name: ThreadPoolExecutor(max_workers=2, thread_name_prefix=f"health-{name}") for name in self._probes
        }

    def check(self) -> HealthReport:
        futures = {name: self._executors[name].submit(self._run, name, probe) for name, probe in self._probes.items()}
        deadline = time.monotonic() + self._timeout_seconds
        components: list[ComponentHealth] = []
        for name, future in futures.items():
            try:
                components.append(future.result(timeout=max(0.0, deadline - time.monotonic())))
            except TimeoutError:
                logger.warning("Health probe timed out: component=%s", name)
                # A probe that never started (its workers are stuck on earlier calls) must not run later
                future.cancel()
                components.append(_down(name, self._timeout_seconds, PROBE_TIMEOUT))
        return HealthReport(tuple(components))

    @staticmethod
    def _run(name: str, probe: Probe) -> ComponentHealth:
        started = time.perf_counter()
        try:
            probe.check()
        except Exception as error:
            # The message can quote hosts and credentials, so only the error type is logged
            logger.warning("Health probe failed: component=%s error=%s", name, type(error).__name__)
            return _down(name, time.perf_counter() - started, PROBE_FAILED)
        return ComponentHealth(name, ComponentStatus.UP, round((time.perf_counter() - started) * 1000))


def _down(name: str, seconds: float, reason_code: str) -> ComponentHealth:
    return ComponentHealth(name, ComponentStatus.DOWN, round(seconds * 1000), reason_code)
