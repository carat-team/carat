"""Connected product parts and mask geometry shared by analysis and cutout."""

from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np

type Array = np.ndarray[Any, Any]
MASK_THRESHOLD = 127
PRODUCT_PART_SHARE = 0.1


@dataclass(frozen=True)
class Components:
    labels: Array
    stats: Array
    product_labels: tuple[int, ...]

    @property
    def product_region(self) -> Array:
        return np.isin(self.labels, self.product_labels)


def validate_mask(mask: Array, shape: tuple[int, int]) -> None:
    if mask.shape != shape or mask.dtype != np.uint8:
        raise ValueError("Expected an 8-bit mask matching the image")


def components(mask: Array) -> Components:
    _, labels, stats, _ = cv2.connectedComponentsWithStats((mask > MASK_THRESHOLD).astype(np.uint8), connectivity=8)
    areas = stats[1:, cv2.CC_STAT_AREA]
    if not areas.size:
        return Components(labels, stats, ())
    largest = int(areas.max())
    parts = tuple(index + 1 for index, area in enumerate(areas) if area >= PRODUCT_PART_SHARE * largest)
    return Components(labels, stats, parts)


def dilate(region: Array, radius: int) -> Array:
    kernel = np.ones((2 * radius + 1, 2 * radius + 1), dtype=np.uint8)
    return cv2.dilate(region.astype(np.uint8), kernel).astype(bool)
