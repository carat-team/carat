from __future__ import annotations

import io
import struct
from typing import TYPE_CHECKING

from carat_algorithms.core import CheckResult, CheckStatus, ProductCard

if TYPE_CHECKING:
    from carat_algorithms.vision.quality.analysis import QualityConfig, QualityResult


class ImageQualityCheck:
    """Evaluate resolution, sharpness, exposure and darkness of every photo."""

    check_id = "image_quality"
    algorithm_version = 2

    def run(self, card: ProductCard) -> CheckResult:
        if not card.photos:
            return self._result(CheckStatus.NOT_CHECKED, "IMAGE_QUALITY_NO_PHOTOS", "У карточки нет фото")

        import cv2
        import numpy as np
        from PIL import Image, ImageOps

        from carat_algorithms.vision.quality.analysis import QualityConfig, analyze_quality

        config = QualityConfig()
        findings: list[tuple[CheckStatus, str, str]] = []
        for number, photo in enumerate(card.photos, start=1):
            try:
                with Image.open(io.BytesIO(photo.content)) as opened:
                    width, height = opened.size
                    orientation = opened.getexif().get(274, 1)
                    original_size = (height, width) if orientation in (5, 6, 7, 8) else (width, height)
                    # JPEG draft avoids decoding full-resolution buffers when supported.
                    opened.draft("RGB", (config.analysis_max_side, config.analysis_max_side))
                    # Pillow forces nearest-neighbor for palette/binary modes unless converted first.
                    working = opened.convert("RGBA") if opened.mode in ("P", "1") else opened
                    working.thumbnail((config.analysis_max_side, config.analysis_max_side), Image.Resampling.BOX)
                    rgba = ImageOps.exif_transpose(working).convert("RGBA")
                    white = Image.new("RGBA", rgba.size, "white")
                    image = Image.alpha_composite(white, rgba).convert("RGB")
                    pixels = np.ascontiguousarray(np.asarray(image)[:, :, ::-1])
            except (
                OSError,
                ValueError,
                SyntaxError,
                TypeError,
                struct.error,
                ZeroDivisionError,
                Image.DecompressionBombError,
            ):
                findings.append(
                    (CheckStatus.REVIEW, "IMAGE_QUALITY_INVALID_PHOTO", f"Фото {number} не удалось прочитать")
                )
                continue
            try:
                quality = analyze_quality(pixels, config, original_size=original_size)
            except (ValueError, cv2.error) as error:
                if isinstance(error, cv2.error) and error.code not in (
                    cv2.Error.StsBadArg,
                    cv2.Error.StsBadSize,
                    cv2.Error.StsUnsupportedFormat,
                    cv2.Error.BadDepth,
                    cv2.Error.BadNumChannels,
                    cv2.Error.StsAssert,
                ):
                    raise
                findings.append(
                    (CheckStatus.REVIEW, "IMAGE_QUALITY_INVALID_PHOTO", f"Фото {number} не удалось проанализировать")
                )
                continue
            if quality.status in (CheckStatus.WARNING, CheckStatus.REVIEW):
                code = "IMAGE_QUALITY_LOW" if quality.status == CheckStatus.WARNING else "IMAGE_QUALITY_REVIEW"
                findings.append((quality.status, code, self._explanation(number, quality, config)))

        for status in (CheckStatus.WARNING, CheckStatus.REVIEW):
            first = next((item for item in findings if item[0] == status), None)
            if first is not None:
                return self._result(status, first[1], "; ".join(item[2] for item in findings))
        return self._result(
            CheckStatus.PASS, "IMAGE_QUALITY_OK", f"Качество фото ({len(card.photos)}) удовлетворяет порогам проверки"
        )

    @staticmethod
    def _explanation(number: int, quality: QualityResult, config: QualityConfig) -> str:
        details = {
            "sharpness": (f"резкость {quality.sharpness_raw:.2f}, ориентиры {config.sharp_lo:g} и {config.sharp_hi:g}"),
            "overexposure": (
                f"доля засвеченных пикселей {quality.clipped_fraction:.3f}, "
                f"ориентиры {config.clip_frac_good:g} и {config.clip_frac_bad:g}"
            ),
            "underexposure": (
                f"яркость p95 {quality.brightness_p95:g}, ориентиры {config.dark_p95_bad:g} и {config.dark_p95_good:g}"
            ),
            "resolution": (
                f"площадь {quality.width * quality.height} пикселей, "
                f"ориентиры {config.res_px_bad} и {config.res_px_good}"
            ),
        }
        action = "недостаточное качество" if quality.status == CheckStatus.WARNING else "требуется проверка"
        return f"Фото {number} ({quality.width}x{quality.height}): {action}, {details[quality.weakest]}"

    def _result(self, status: CheckStatus, reason_code: str, explanation: str) -> CheckResult:
        return CheckResult(
            check_id=self.check_id,
            status=status,
            reason_code=reason_code,
            explanation=explanation,
            field_refs=("photos",),
            algorithm_version=self.algorithm_version,
        )
