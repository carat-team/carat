"""Check card photos for visual signals associated with AI generation."""

from __future__ import annotations

from pathlib import Path

from carat_algorithms.core import CheckResult, CheckStatus, ProductCard
from carat_algorithms.vision.image_origin.detector import (
    GENERATION_LOGIT,
    WEIGHTS_FILENAME,
    WEIGHTS_SUBDIRECTORY,
    PixelDetector,
    UnsupportedPhotoError,
)


class ImageOriginCheck:
    check_id = "image_origin"
    algorithm_version = 2

    def __init__(self, weights_dir: Path | None = None) -> None:
        path = weights_dir / WEIGHTS_SUBDIRECTORY / WEIGHTS_FILENAME if weights_dir is not None else None
        self._detector = PixelDetector(path) if path is not None else None

    def run(self, card: ProductCard) -> CheckResult:
        if not card.photos:
            return self._result(CheckStatus.NOT_CHECKED, "NO_PHOTOS", "У карточки нет фото")

        detector = self._detector
        if detector is None or not detector.available:
            return self._result(
                CheckStatus.NOT_CHECKED,
                "WEIGHTS_MISSING",
                "Локальная модель проверки происхождения фото не установлена",
            )

        unreadable_photo: int | None = None
        for index, photo in enumerate(card.photos, start=1):
            try:
                logit = detector.score(photo.content)
            except UnsupportedPhotoError:
                if unreadable_photo is None:
                    unreadable_photo = index
                continue
            if logit >= GENERATION_LOGIT:
                return self._result(
                    CheckStatus.WARNING,
                    "AI_SIGNAL",
                    f"Фото {index}: найдены признаки ИИ-генерации, нужна ручная проверка",
                )
        if unreadable_photo is not None:
            return self._result(
                CheckStatus.REVIEW, "UNSUPPORTED_PHOTO", f"Фото {unreadable_photo}: не удалось обработать изображение"
            )
        return self._result(CheckStatus.REVIEW, "INCONCLUSIVE", "По признакам изображения происхождение не установлено")

    def _result(self, status: CheckStatus, reason: str, explanation: str) -> CheckResult:
        return CheckResult(
            check_id=self.check_id,
            status=status,
            reason_code=f"IMAGE_ORIGIN_{reason}",
            explanation=explanation,
            field_refs=("photos",),
            algorithm_version=self.algorithm_version,
        )
