"""Entry point for `uvicorn carat_backend.main:create_app --factory`."""

from carat_backend.rest.app import create_app

__all__ = ["create_app"]
