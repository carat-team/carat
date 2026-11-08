"""Configuration for checks registered by the application."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from carat_algorithms.text.brand_value import BrandValueConfig


@dataclass(frozen=True)
class CheckConfig:
    """Optional configuration for checks created by the registry."""

    brand_value_config: BrandValueConfig | None = None
