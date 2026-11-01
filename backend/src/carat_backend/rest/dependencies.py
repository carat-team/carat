from typing import Annotated

from fastapi import Depends, Request

from carat_backend.bootstrap import Services


def get_services(request: Request) -> Services:
    services: Services = request.app.state.services
    return services


ServicesDependency = Annotated[Services, Depends(get_services)]
