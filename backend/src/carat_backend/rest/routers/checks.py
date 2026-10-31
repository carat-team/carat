import uuid

from carat_algorithms.core import CheckResult
from fastapi import APIRouter

from carat_backend.rest.dependencies import ServicesDependency

router = APIRouter(prefix="/api/products/{product_id}/check", tags=["checks"])


@router.post("")
def check_product(product_id: uuid.UUID, services: ServicesDependency) -> list[CheckResult]:
    return services.checks.check(product_id)
