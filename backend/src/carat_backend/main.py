from fastapi import FastAPI

from carat_backend.api import health


def create_app() -> FastAPI:
    app = FastAPI(title="Carat")
    app.include_router(health.router)
    return app
