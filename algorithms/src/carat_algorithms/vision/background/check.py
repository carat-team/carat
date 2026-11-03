from __future__ import annotations

import io
import struct
import threading
from pathlib import Path
from typing import TYPE_CHECKING

from carat_algorithms.core import CheckResult, CheckStatus, ProductCard

if TYPE_CHECKING:
    from carat_algorithms.vision.background.segmentation import Segmenter


class BackgroundCheck:
    """Check all card photos; warnings and undecidable photos cannot be hidden by a clean one."""

    check_id = "background"
    algorithm_version = 2

    def __init__(self, weights_dir: Path | None = None, *, segmenter: Segmenter | None = None) -> None:
        self._weights_dir = weights_dir
        self._segmenter = segmenter
        self._lock = threading.Lock()

    def run(self, card: ProductCard) -> CheckResult:
        if not card.photos:
            return self._result(CheckStatus.NOT_CHECKED, "BACKGROUND_NO_PHOTOS", "У карточки нет фото")
        from carat_algorithms.vision.background.segmentation import WEIGHTS_FILENAME, WEIGHTS_SUBDIRECTORY

        if self._segmenter is None and (
            self._weights_dir is None or not (self._weights_dir / WEIGHTS_SUBDIRECTORY / WEIGHTS_FILENAME).is_file()
        ):
            return self._result(
                CheckStatus.NOT_CHECKED, "BACKGROUND_WEIGHTS_MISSING", "Локальная модель проверки фона не установлена"
            )
        results = [self._photo_result(photo.content) for photo in card.photos]
        priority = {CheckStatus.PASS: 0, CheckStatus.REVIEW: 1, CheckStatus.WARNING: 2}
        number, result = max(enumerate(results, start=1), key=lambda item: priority[item[1].status])
        return self._result(result.status, result.reason_code, f"Фото {number}: {result.explanation}")

    def _get_segmenter(self) -> Segmenter:
        with self._lock:
            if self._segmenter is None:
                from carat_algorithms.vision.background.segmentation import ISNetSegmenter

                if self._weights_dir is None:
                    raise RuntimeError("Background model directory was not configured")
                self._segmenter = ISNetSegmenter(self._weights_dir)
            return self._segmenter

    def _photo_result(self, content: bytes) -> CheckResult:
        import numpy as np
        from PIL import Image, ImageOps

        from carat_algorithms.vision.background.analysis import analyze_background

        try:
            with Image.open(io.BytesIO(content)) as opened:
                opened.draft("RGB", (512, 512))
                # Normalize indexed/16-bit modes and color-key alpha before filtered resizing.
                needs_conversion = opened.mode not in ("RGB", "RGBA", "L", "LA") or "transparency" in opened.info
                working = opened.convert("RGBA") if needs_conversion else opened
                working.thumbnail((512, 512), Image.Resampling.BILINEAR)
                rgba = ImageOps.exif_transpose(working).convert("RGBA")
                white = Image.new("RGBA", rgba.size, "white")
                image = Image.alpha_composite(white, rgba).convert("RGB")
        except (
            OSError,
            ValueError,
            SyntaxError,
            TypeError,
            struct.error,
            ZeroDivisionError,
            Image.DecompressionBombError,
        ):
            return self._result(
                CheckStatus.REVIEW, "BACKGROUND_INVALID_PHOTO", "Не удалось открыть фото для проверки фона"
            )
        try:
            mask = self._get_segmenter().segment(image)
            analysis = analyze_background(np.asarray(image), mask)
        except ValueError:
            return self._result(
                CheckStatus.REVIEW, "BACKGROUND_MASK_INVALID", "Не удалось получить корректную маску товара"
            )
        return self._result(analysis.status, analysis.reason_code, analysis.explanation)

    def _result(self, status: CheckStatus, reason_code: str, explanation: str) -> CheckResult:
        return CheckResult(
            check_id=self.check_id,
            status=status,
            reason_code=reason_code,
            explanation=explanation,
            field_refs=("photos",),
            algorithm_version=self.algorithm_version,
        )
