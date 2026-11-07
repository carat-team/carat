"""Configuration types for the brand value check."""

from dataclasses import dataclass
from math import isfinite

from carat_algorithms.text.brand_value.normalization import normalize_brand_value


@dataclass(frozen=True)
class ForbiddenBrandValue:
    """One approved forbidden value and its optional fuzzy distance threshold."""

    value: str
    max_distance: float | None = None

    def __post_init__(self) -> None:
        if not normalize_brand_value(self.value):
            raise ValueError("A forbidden brand value must not be empty")
        if self.max_distance is not None and (not isfinite(self.max_distance) or not 0.0 <= self.max_distance <= 1.0):
            raise ValueError("A Jaro-Winkler distance threshold must be between 0 and 1")


@dataclass(frozen=True)
class BrandValueConfig:
    """Approved rules supplied by the application that creates the check."""

    forbidden_values: tuple[ForbiddenBrandValue, ...] = ()

    def __post_init__(self) -> None:
        normalized_values = [normalize_brand_value(item.value) for item in self.forbidden_values]
        if len(normalized_values) != len(set(normalized_values)):
            raise ValueError("Forbidden brand values must be unique after normalization")
