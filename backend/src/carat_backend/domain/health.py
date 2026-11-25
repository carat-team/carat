"""Health report models shared by the health service and the API adapters."""

from dataclasses import dataclass
from enum import StrEnum


class ComponentStatus(StrEnum):
    UP = "up"
    DOWN = "down"


@dataclass(frozen=True)
class ComponentHealth:
    name: str
    status: ComponentStatus
    latency_ms: int
    # A short fixed code, never the raw error text: that can quote hosts and credentials
    reason_code: str | None = None


@dataclass(frozen=True)
class HealthReport:
    components: tuple[ComponentHealth, ...]

    @property
    def ready(self) -> bool:
        return all(component.status is ComponentStatus.UP for component in self.components)
