import uuid
from typing import Annotated

from fastapi import APIRouter, Body

from carat_backend.rest.dependencies import ServicesDependency
from carat_backend.rest.schemas.products import ProductCreate, ProductListItem, ProductOut, ProductUpdate

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("")
def list_products(services: ServicesDependency) -> list[ProductListItem]:
    return [ProductListItem.from_domain(product) for product in services.products.list()]


@router.post("", status_code=201)
def create_product(services: ServicesDependency, body: Annotated[ProductCreate | None, Body()] = None) -> ProductOut:
    attributes = (body or ProductCreate()).attributes.model_dump(by_alias=True, exclude_none=True)
    return ProductOut.from_domain(services.products.create(attributes))


@router.get("/{product_id}")
def get_product(product_id: uuid.UUID, services: ServicesDependency) -> ProductOut:
    return ProductOut.from_domain(services.products.get(product_id))


@router.patch("/{product_id}")
def update_product(product_id: uuid.UUID, body: ProductUpdate, services: ServicesDependency) -> ProductOut:
    changes = body.attributes.model_dump(by_alias=True, exclude_unset=True)
    return ProductOut.from_domain(services.products.update(product_id, changes))
