import math
from dataclasses import asdict, dataclass
from typing import Optional, Tuple

import cv2
import numpy as np


@dataclass(frozen=True)
class QualityConfig:
    
    analysis_max_side: int = 1024

    sharp_grid: int = 8
    sharp_percentile: float = 90.0
    sharp_lo: float = 60.0
    sharp_hi: float = 300.0

    clip_level: int = 250
    clip_ignore_background: bool = True
    bg_level: int = 235
    min_object_fraction: float = 0.005
    clip_frac_good: float = 0.05
    clip_frac_bad: float = 0.50

    dark_p95_bad: float = 40.0
    dark_p95_good: float = 120.0

    res_px_bad: int = 160_000 # Изображения ~400х400
    res_px_good: int = 2_000_000 # Изображения ~1920х1080
    res_curve_x: Tuple[float, ...] = (0.0, 30.0, 60.0, 100.0)
    res_curve_y: Tuple[float, ...] = (50.0, 70.0, 90.0, 100.0)

    reject_max: int = 60
    review_max: int = 80


@dataclass(frozen=True)
class QualityResult:
    # Размер изображения
    width: int
    height: int
    # Сырые значения параметров
    sharpness_raw: float
    clipped_fraction: float
    background_fraction: float
    brightness_p95: float
    # Сами оценки 0-100
    sharpness: int
    overexposure: int
    underexposure: int
    resolution: int
    # Вердикты
    overall: int
    verdict: str
    weakest: str

    def to_dict(self) -> dict:
        return asdict(self)



_SCORE_KEYS = ("overexposure", "underexposure", "resolution", "sharpness")


def _linear(value: float, bad: float, good: float) -> float:
    """Линейно отображает [bad .. good] в [0 .. 100] с обрезкой."""
    if good == bad:
        return 100.0
    t = (value - bad) / (good - bad)
    return 100.0 * min(1.0, max(0.0, t))


def _to_gray(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        return image
    if image.ndim == 3 and image.shape[2] == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if image.ndim == 3 and image.shape[2] == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
    raise ValueError(f"Unsupported image shape: {image.shape}")


def _downscale(gray: np.ndarray, max_side: int) -> np.ndarray:
    h, w = gray.shape
    scale = max_side / max(h, w)
    if scale >= 1.0:
        return gray
    size = (max(1, round(w * scale)), max(1, round(h * scale)))
    return cv2.resize(gray, size, interpolation=cv2.INTER_AREA)


def _sharpness_raw(gray: np.ndarray, config: QualityConfig) -> float:

    smoothed = cv2.GaussianBlur(gray, (3, 3), 0)
    laplacian = cv2.Laplacian(smoothed, cv2.CV_64F)

    grid = config.sharp_grid
    tile_h, tile_w = laplacian.shape[0] // grid, laplacian.shape[1] // grid
    if tile_h < 8 or tile_w < 8:
        return float(laplacian.var())

    cropped = laplacian[: tile_h * grid, : tile_w * grid]
    tiles = cropped.reshape(grid, tile_h, grid, tile_w).var(axis=(1, 3))
    return float(np.percentile(tiles, config.sharp_percentile))


def _clipped_fraction(gray: np.ndarray, config: QualityConfig) -> Tuple[float, float]:
    clipped = gray >= config.clip_level
    if not config.clip_ignore_background:
        return float(clipped.mean()), 0.0 # Доля белых фоновых пикселей

    near_white = (gray >= config.bg_level).astype(np.uint8)
    _, labels = cv2.connectedComponents(near_white, connectivity=4)
    border = np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]])
    border_labels = np.unique(border)
    background = np.isin(labels, border_labels[border_labels != 0])
    background_fraction = float(background.mean())

    object_area = gray.size - int(np.count_nonzero(background))
    if object_area < config.min_object_fraction * gray.size:
        return 1.0, background_fraction

    interior_clipped = int(np.count_nonzero(clipped & ~background))
    return interior_clipped / object_area, background_fraction


def verdict_for(score: int, config: Optional[QualityConfig] = None) -> str:
    cfg = config or QualityConfig()
    if score <= cfg.reject_max:
        return "reject"
    if score <= cfg.review_max:
        return "review"
    return "ok"


def analyze_quality(image: np.ndarray, config: Optional[QualityConfig] = None) -> QualityResult:
    cfg = config or QualityConfig()
    if image is None or image.size == 0:
        raise ValueError("Empty image")

    height, width = image.shape[:2]
    small = _downscale(_to_gray(image), cfg.analysis_max_side)

    sharpness_raw = _sharpness_raw(small, cfg)
    clipped_fraction, background_fraction = _clipped_fraction(small, cfg)
    brightness_p95 = float(np.percentile(small, 95))

    resolution_linear = _linear(
        math.log(width * height),
        math.log(cfg.res_px_bad),
        math.log(cfg.res_px_good),
    )
    scores = {
        "sharpness": _linear(
            math.log1p(sharpness_raw),
            math.log1p(cfg.sharp_lo),
            math.log1p(cfg.sharp_hi),
        ),
        "overexposure": _linear(
            clipped_fraction, cfg.clip_frac_bad, cfg.clip_frac_good
        ),
        "underexposure": _linear(
            brightness_p95, cfg.dark_p95_bad, cfg.dark_p95_good
        ),
        "resolution": float(
            np.interp(resolution_linear, cfg.res_curve_x, cfg.res_curve_y)
        ),
    }
    scores = {k: int(round(v)) for k, v in scores.items()}

    weakest = min(_SCORE_KEYS, key=lambda k: scores[k])
    overall = scores[weakest]

    return QualityResult(
        width=width,
        height=height,
        sharpness_raw=sharpness_raw,
        clipped_fraction=clipped_fraction,
        background_fraction=background_fraction,
        brightness_p95=brightness_p95,
        overall=overall,
        verdict=verdict_for(overall, cfg),
        weakest=weakest,
        **scores,
    )


def analyze_quality_file(path: str, config: Optional[QualityConfig] = None) -> QualityResult:
    image = cv2.imread(path)
    if image is None:
        raise ValueError(f"Cannot read image: {path}")
    return analyze_quality(image, config)
