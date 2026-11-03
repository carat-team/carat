"""Pure background analysis ported from the original PR's Java analyzer.

Fit a quadratic Lab surface to allow smooth gradients, then detect texture and
foreign components. Geometry and intermediate diagnostics stay internal.
"""

import math
from dataclasses import dataclass

import cv2
import numpy as np

from carat_algorithms.core import CheckStatus
from carat_algorithms.vision.background.masks import MASK_THRESHOLD, Array, components, dilate, validate_mask

MIN_OBJECT_SHARE = 0.005
NEAR_DELTA_E = 10
FAR_DELTA_E = 25
CLEAN_UNIFORMITY = 0.95
CLEAN_EDGE_DENSITY = 0.02


@dataclass(frozen=True)
class Box:
    x: int
    y: int
    width: int
    height: int
    area_share: float


@dataclass(frozen=True)
class ForeignObject:
    box: Box
    source: str


@dataclass(frozen=True)
class BackgroundAnalysis:
    status: CheckStatus
    reason_code: str
    explanation: str
    main_box: Box | None = None
    foreign_objects: tuple[ForeignObject, ...] = ()
    background_color: str | None = None


def _box(region: Array, total: int, scale: float) -> Box:
    rows, columns = np.nonzero(region)
    return Box(
        math.floor(int(columns.min()) * scale + 0.5),
        math.floor(int(rows.min()) * scale + 0.5),
        math.floor((int(columns.max() - columns.min()) + 1) * scale + 0.5),
        math.floor((int(rows.max() - rows.min()) + 1) * scale + 0.5),
        round(int(region.sum()) / total, 4),
    )


def _background_model(lab: Array, background: Array) -> Array:
    height, width = background.shape
    rows, columns = np.indices((height, width), dtype=np.float64) / max(height, width)
    features = np.stack((np.ones_like(rows), columns, rows, columns**2, columns * rows, rows**2), axis=-1)
    selected = np.flatnonzero(background)
    selected = selected[:: max(1, len(selected) // 20_000)]
    coefficients, _, _, _ = np.linalg.lstsq(features.reshape(-1, 6)[selected], lab.reshape(-1, 3)[selected], rcond=None)
    return features @ coefficients


def analyze_background(image: Array, mask: Array, scale: float = 1.0) -> BackgroundAnalysis:
    """Analyze an RGB uint8 image and its soft uint8 mask of the same size."""
    height, width = image.shape[:2]
    validate_mask(mask, (height, width))
    labeling = components(mask)
    if not labeling.product_labels:
        return BackgroundAnalysis(CheckStatus.REVIEW, "BACKGROUND_NO_OBJECT", "На фото не удалось выделить товар")

    total = height * width
    min_area = MIN_OBJECT_SHARE * total
    product = labeling.product_region
    main_box = _box(product, total, scale)
    foreign: list[ForeignObject] = []
    for label in range(1, len(labeling.stats)):
        if label not in labeling.product_labels and labeling.stats[label, cv2.CC_STAT_AREA] >= min_area:
            foreign.append(ForeignObject(_box(labeling.labels == label, total, scale), "mask"))

    margin = max(3, math.floor(0.02 * min(height, width) + 0.5))
    objects = mask > MASK_THRESHOLD
    background = ~dilate(objects, margin // 2)
    if int(background.sum()) < min_area:
        background = ~objects
    if int(background.sum()) < max(6, min_area):
        return BackgroundAnalysis(
            CheckStatus.REVIEW, "BACKGROUND_AREA_TOO_SMALL", "На фото недостаточно фона для проверки", main_box
        )

    lab = cv2.cvtColor(image.astype(np.float32) / 255, cv2.COLOR_RGB2LAB).astype(np.float64)
    model = _background_model(lab, background)
    delta = np.linalg.norm(lab - model, axis=2)
    uniformity = float(np.mean(delta[background] < NEAR_DELTA_E))
    gray = np.floor(image.astype(np.float64) @ np.array([0.299, 0.587, 0.114]) + 0.5).astype(np.uint8)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3, L2gradient=False) > 0
    edge_density = float(np.mean(edges[background]))

    near_product = dilate(product, margin)
    far = ((delta > FAR_DELTA_E) & background).astype(np.uint8)
    opened = cv2.morphologyEx(far, cv2.MORPH_OPEN, np.ones((5, 5), dtype=np.uint8))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(opened, connectivity=8)
    for label in range(1, count):
        region = labels == label
        if stats[label, cv2.CC_STAT_AREA] >= min_area and not np.any(region & near_product):
            foreign.append(ForeignObject(_box(region, total, scale), "background"))

    median_lab = np.median(model[background], axis=0).astype(np.float32).reshape(1, 1, 3)
    rgb = np.clip(np.rint(cv2.cvtColor(median_lab, cv2.COLOR_LAB2RGB)[0, 0] * 255), 0, 255).astype(np.uint8)
    color = "#" + "".join(f"{int(channel):02x}" for channel in rgb)
    if foreign:
        return BackgroundAnalysis(
            CheckStatus.WARNING,
            "BACKGROUND_FOREIGN_OBJECTS",
            f"На фото обнаружены посторонние объекты: {len(foreign)}",
            main_box,
            tuple(foreign),
            color,
        )
    if uniformity >= CLEAN_UNIFORMITY and edge_density <= CLEAN_EDGE_DENSITY:
        return BackgroundAnalysis(CheckStatus.PASS, "BACKGROUND_CLEAN", "Фон на фото однородный", main_box, (), color)
    return BackgroundAnalysis(
        CheckStatus.WARNING,
        "BACKGROUND_NOISY",
        "Фон на фото неоднородный или содержит много деталей",
        main_box,
        (),
        color,
    )
