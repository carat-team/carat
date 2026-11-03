"""Database schema: an EAV model with one row per card attribute (CARAT_MVP, sheet 04)."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from carat_backend.domain.models import ProductStatus


class Base(DeclarativeBase):
    pass


class ProductRow(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(String(32), default=ProductStatus.DRAFT.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    attributes: Mapped[list["ProductAttributeRow"]] = relationship(
        cascade="all, delete-orphan", lazy="selectin", order_by="ProductAttributeRow.attribute_key"
    )
    photos: Mapped[list["PhotoRow"]] = relationship(
        cascade="all, delete-orphan", lazy="selectin", order_by="PhotoRow.created_at"
    )


class ProductAttributeRow(Base):
    """One card field: attribute_key is the API name (fullName, volume, ...), value_json its value."""

    __tablename__ = "product_attributes"

    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), primary_key=True)
    attribute_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value_json: Mapped[Any] = mapped_column(JSONB)


class PhotoRow(Base):
    """Photo metadata. The image itself lives in object storage under object_key."""

    __tablename__ = "product_photos"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    perspective: Mapped[str] = mapped_column(String(64))
    package_id: Mapped[str | None] = mapped_column(String(64))
    content_type: Mapped[str] = mapped_column(String(64))
    size_bytes: Mapped[int] = mapped_column(Integer)
    object_key: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
