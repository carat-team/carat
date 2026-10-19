"""Stable public API for rule-based product quantity validation.

Consumers should import from this package instead of internal modules. This
keeps call sites stable while parsing and validation rules evolve separately.
"""

from .checker import check_product_card, check_quantity, check_volume
from .config import (
    GENERIC_PROFILE,
    NAME,
    PERFUMERY_PROFILE,
    QuantityProfile,
    UNIT,
    VALUE,
)

__all__ = [
    "GENERIC_PROFILE",
    "NAME",
    "PERFUMERY_PROFILE",
    "QuantityProfile",
    "UNIT",
    "VALUE",
    "check_product_card",
    "check_quantity",
    "check_volume",
]
