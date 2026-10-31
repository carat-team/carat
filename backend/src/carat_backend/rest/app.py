from fastapi import FastAPI

from carat_backend.bootstrap import build_services
from carat_backend.rest.errors import register_error_handlers
from carat_backend.rest.routers import checks, health, photos, products
from carat_backend.settings import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    app = FastAPI(title="Carat")
    app.state.services = build_services(settings or get_settings())
    register_error_handlers(app)
    for module in (health, products, photos, checks):
        app.include_router(module.router)
    return app
