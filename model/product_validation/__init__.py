"""Rule-based validation of structured product-card attributes."""

from .volume_check import (
    GENERIC_PROFILE,
    PERFUMERY_PROFILE,
    QuantityProfile,
    check_product_card,
    check_quantity,
    check_volume,
)

__all__ = [
    "GENERIC_PROFILE",
    "PERFUMERY_PROFILE",
    "QuantityProfile",
    "check_product_card",
    "check_quantity",
    "check_volume",
]
