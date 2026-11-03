import io

from carat_algorithms.core import CheckResult, CheckStatus, ProductCard


class ImageQualityCheck:
    """Evaluate resolution, sharpness, exposure and darkness of every photo."""

    check_id = "image_quality"
    algorithm_version = 1

    def run(self, card: ProductCard) -> CheckResult:
        if not card.photos:
            return self._result(CheckStatus.NOT_CHECKED, "IMAGE_QUALITY_NO_PHOTOS", "У карточки нет фото")

        import numpy as np
        from PIL import Image, ImageOps

        from carat_algorithms.vision.quality.analysis import analyze_quality

        findings: list[tuple[CheckStatus, str, str]] = []
        labels = {
            "sharpness": "резкость",
            "overexposure": "засветка",
            "underexposure": "освещённость",
            "resolution": "разрешение",
        }
        for number, photo in enumerate(card.photos, start=1):
            try:
                with Image.open(io.BytesIO(photo.content)) as image:
                    oriented = ImageOps.exif_transpose(image).convert("RGB")
                    pixels = np.ascontiguousarray(np.asarray(oriented)[:, :, ::-1])
                quality = analyze_quality(pixels)
            except (OSError, ValueError, SyntaxError, Image.DecompressionBombError):
                findings.append(
                    (CheckStatus.REVIEW, "IMAGE_QUALITY_INVALID_PHOTO", f"Фото {number} не удалось прочитать")
                )
                continue
            if quality.status == CheckStatus.WARNING:
                findings.append(
                    (
                        quality.status,
                        "IMAGE_QUALITY_LOW",
                        f"Фото {number}: недостаточное качество, показатель - {labels[quality.weakest]}",
                    )
                )
            elif quality.status == CheckStatus.REVIEW:
                findings.append(
                    (
                        quality.status,
                        "IMAGE_QUALITY_REVIEW",
                        f"Фото {number}: требуется проверить показатель {labels[quality.weakest]}",
                    )
                )

        for status in (CheckStatus.WARNING, CheckStatus.REVIEW):
            first = next((item for item in findings if item[0] == status), None)
            if first is not None:
                return self._result(status, first[1], "; ".join(item[2] for item in findings))
        return self._result(CheckStatus.PASS, "IMAGE_QUALITY_OK", "Качество фотографий удовлетворяет порогам проверки")

    def _result(self, status: CheckStatus, reason_code: str, explanation: str) -> CheckResult:
        return CheckResult(
            check_id=self.check_id,
            status=status,
            reason_code=reason_code,
            explanation=explanation,
            field_refs=("photos",),
            algorithm_version=self.algorithm_version,
        )
