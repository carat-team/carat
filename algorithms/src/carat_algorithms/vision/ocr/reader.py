"""
Label text recognition with EasyOCR. Ported from inference/app/detectors/ocr_detector.py (PR #21).
"""

import io
import threading
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast

DEFAULT_LANGUAGES = ("ru", "en")
DEFAULT_MIN_CONFIDENCE = 0.3
# Large phone photos make OCR on CPU slow, so it runs on a downscaled copy
DEFAULT_MAX_IMAGE_SIDE = 1600


@dataclass(frozen=True)
class TextBlock:
    text: str
    confidence: float


class _EasyOcrReader(Protocol):
    def readtext(self, image: object) -> list[tuple[object, str, float]]: ...


def downscaled_size(width: int, height: int, max_side: int) -> tuple[int, int]:
    """Size that fits the longer side into max_side; images that already fit keep their size."""
    scale = min(1.0, max_side / max(width, height))
    return round(width * scale), round(height * scale)


class OcrReader:
    """Loads the EasyOCR model on first use, once per instance, from weights_directory (no downloads)."""

    def __init__(
        self,
        weights_directory: Path,
        languages: Sequence[str] = DEFAULT_LANGUAGES,
        min_confidence: float = DEFAULT_MIN_CONFIDENCE,
        max_image_side: int = DEFAULT_MAX_IMAGE_SIDE,
    ) -> None:
        self.weights_directory = weights_directory
        self.languages = tuple(languages)
        self.min_confidence = min_confidence
        self.max_image_side = max_image_side
        self._reader: _EasyOcrReader | None = None
        self._lock = threading.Lock()

    def read_text(self, image_bytes: bytes) -> list[TextBlock]:
        import numpy
        from PIL import Image, ImageOps

        image = ImageOps.exif_transpose(Image.open(io.BytesIO(image_bytes))).convert("RGB")
        size = downscaled_size(image.width, image.height, self.max_image_side)
        if size != image.size:
            image = image.resize(size)

        return [
            TextBlock(text, float(confidence))
            for _, text, confidence in self._get_reader().readtext(numpy.asarray(image))
            if confidence >= self.min_confidence
        ]

    def _get_reader(self) -> _EasyOcrReader:
        with self._lock:
            if self._reader is None:
                import easyocr  # pyright: ignore[reportMissingTypeStubs]

                reader = easyocr.Reader(  # pyright: ignore[reportUnknownMemberType]
                    list(self.languages),
                    gpu=False,
                    verbose=False,
                    model_storage_directory=str(self.weights_directory),
                    download_enabled=False,
                )
                self._reader = cast(_EasyOcrReader, reader)
            return self._reader
