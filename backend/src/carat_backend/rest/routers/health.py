from fastapi import APIRouter, Response, status

from carat_backend.rest.dependencies import ServicesDependency
from carat_backend.rest.schemas.health import ReadinessResponse

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness: the process answers. It must not depend on anything else."""
    return {"status": "ok"}


@router.get("/health/ready", responses={503: {"model": ReadinessResponse}})
def ready(services: ServicesDependency, response: Response) -> ReadinessResponse:
    """Readiness: 200 when the database and the object storage work, 503 with the details otherwise."""
    report = services.health.check()
    if not report.ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse.from_report(report)
