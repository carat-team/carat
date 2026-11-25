from typing import Literal, Self

from pydantic import BaseModel

from carat_backend.domain.health import ComponentStatus, HealthReport


class ComponentHealthResponse(BaseModel):
    status: ComponentStatus
    latency_ms: int
    reason_code: str | None = None


class ReadinessResponse(BaseModel):
    status: Literal["ok", "unavailable"]
    components: dict[str, ComponentHealthResponse]

    @classmethod
    def from_report(cls, report: HealthReport) -> Self:
        return cls(
            status="ok" if report.ready else "unavailable",
            components={
                component.name: ComponentHealthResponse(
                    status=component.status, latency_ms=component.latency_ms, reason_code=component.reason_code
                )
                for component in report.components
            },
        )
