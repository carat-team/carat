"""Run a pinned AI-image detector locally with one ONNX Runtime CPU thread."""

from __future__ import annotations

import hashlib
import io
import math
import struct
import threading
from collections.abc import Callable
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, cast

if TYPE_CHECKING:
    import numpy as np

type FloatPixels = np.ndarray[tuple[int, ...], np.dtype[np.float32]]

WEIGHTS_SUBDIRECTORY = "image_origin"
WEIGHTS_FILENAME = "community-forensics-frontier-int8.onnx"
WEIGHTS_SHA256 = "6c5720f444c400bdfd8bf369ae151de7b736d6749a9ec72da343fb392cafe4eb"
WEIGHTS_BYTES = 22_922_295
GENERATION_LOGIT = 1.359375
MAX_IMAGE_PIXELS = 12_000_000
MIN_IMAGE_EDGE = 224


class _Options(Protocol):
    intra_op_num_threads: int
    inter_op_num_threads: int


class _Session(Protocol):
    def run(self, output_names: list[str], input_feed: dict[str, FloatPixels]) -> list[object]: ...


class UnsupportedPhotoError(ValueError):
    """Image cannot safely be passed to the detector."""


def preprocess(content: bytes) -> FloatPixels:
    import numpy as np
    from PIL import Image

    try:
        with Image.open(io.BytesIO(content), formats=["JPEG", "PNG", "WEBP"]) as photo:
            short, long = sorted(photo.size)
            if short * long > MAX_IMAGE_PIXELS or short < MIN_IMAGE_EDGE or long > short * 8:
                raise UnsupportedPhotoError("Photo is outside the detector's size limits")
            if getattr(photo, "is_animated", False):
                raise UnsupportedPhotoError("Animated photos are unsupported")
            width, height = (440 * side // short for side in photo.size)
            if photo.mode == "RGB":
                resized = photo.resize((width, height), Image.Resampling.BILINEAR)
            else:
                with photo.convert("RGB") as rgb:
                    resized = rgb.resize((width, height), Image.Resampling.BILINEAR)
            with resized:
                left, top = (width - 384) // 2, (height - 384) // 2
                with resized.crop((left, top, left + 384, top + 384)) as crop:
                    values = np.asarray(crop, dtype=np.float32)
    except UnsupportedPhotoError:
        raise
    except (OSError, ValueError, SyntaxError, TypeError, struct.error, Image.DecompressionBombError) as error:
        raise UnsupportedPhotoError("Photo could not be decoded") from error
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    return np.ascontiguousarray(((values / 255.0 - mean) / std).transpose(2, 0, 1)[None])


class PixelDetector:
    """Lazily load one checksum-verified model per check."""

    def __init__(self, weights_path: Path) -> None:
        self._weights_path = weights_path
        self._lock = threading.Lock()
        self._infer: Callable[[FloatPixels], float] | None = None

    @property
    def available(self) -> bool:
        return self._weights_path.is_file()

    def score(self, content: bytes) -> float:
        with self._lock:
            pixels = preprocess(content)
            if self._infer is None:
                self._infer = self._load()
            logit = self._infer(pixels)
            if not math.isfinite(logit):
                raise RuntimeError("Image-origin detector returned a non-finite logit")
            return logit

    def _load(self) -> Callable[[FloatPixels], float]:
        import numpy as np

        if self._weights_path.stat().st_size != WEIGHTS_BYTES:
            raise RuntimeError("Unexpected image-origin model size")
        with self._weights_path.open("rb") as file:
            if hashlib.file_digest(file, "sha256").hexdigest() != WEIGHTS_SHA256:
                raise RuntimeError("Unexpected image-origin model SHA-256")

        runtime = import_module("onnxruntime")
        options_factory = cast(Callable[[], _Options], runtime.SessionOptions)
        session_factory = cast(Callable[..., _Session], runtime.InferenceSession)
        options = options_factory()
        options.intra_op_num_threads = 1
        options.inter_op_num_threads = 1
        session = session_factory(str(self._weights_path), sess_options=options, providers=["CPUExecutionProvider"])

        def infer(pixels: FloatPixels) -> float:
            outputs = session.run(["logits"], {"images": pixels})
            output: object = outputs[0]
            if not isinstance(output, np.ndarray):
                raise RuntimeError("Image-origin detector returned a non-array output")
            logits = cast(FloatPixels, output)
            if logits.shape != (1, 1):
                raise RuntimeError("Image-origin detector returned an invalid shape")
            return float(logits[0, 0])

        return infer
