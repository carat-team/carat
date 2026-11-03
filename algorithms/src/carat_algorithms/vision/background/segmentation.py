"""Local ISNet inference with rembg's published preprocessing, without downloads."""

import threading
from collections.abc import Callable
from importlib import import_module
from pathlib import Path
from typing import Protocol, cast

import numpy as np
from PIL import Image

from carat_algorithms.vision.background.masks import Array

WEIGHTS_SUBDIRECTORY = "isnet"
WEIGHTS_FILENAME = "isnet-general-use.onnx"


class Segmenter(Protocol):
    def segment(self, image: Image.Image) -> Array: ...


class _Options(Protocol):
    intra_op_num_threads: int
    inter_op_num_threads: int


class _Input(Protocol):
    @property
    def name(self) -> str: ...


class _Session(Protocol):
    def get_inputs(self) -> list[_Input]: ...
    def run(self, output_names: None, input_feed: dict[str, Array]) -> list[Array]: ...


def normalize(image: Image.Image) -> Array:
    """Match rembg DisSession: RGB Lanczos 1024, divide by image max, subtract 0.5."""
    resized = image.convert("RGB").resize((1024, 1024), Image.Resampling.LANCZOS)
    values = np.asarray(resized, dtype=np.float32)
    values = values / max(float(values.max()), 1e-6) - 0.5
    return np.transpose(values, (2, 0, 1))[None].astype(np.float32)


def output_mask(output: Array, size: tuple[int, int]) -> Array:
    if output.ndim != 4 or output.shape[0] != 1 or output.shape[1] != 1 or not output.size:
        raise ValueError("Model returned an invalid mask shape")
    values = output[0, 0].astype(np.float32)
    if values.ndim != 2 or not np.isfinite(values).all():
        raise ValueError("Model returned an invalid mask")
    low, high = float(values.min()), float(values.max())
    normalized = np.zeros_like(values) if high <= low else (values - low) / (high - low)
    mask = Image.fromarray((normalized * 255).astype(np.uint8))
    return np.asarray(mask.resize(size, Image.Resampling.LANCZOS))


class ISNetSegmenter:
    """One lazy CPU session per check instance, serialized for bounded memory use."""

    def __init__(self, weights_dir: Path) -> None:
        self.weights_path = weights_dir / WEIGHTS_SUBDIRECTORY / WEIGHTS_FILENAME
        self._session: _Session | None = None
        self._lock = threading.Lock()

    def segment(self, image: Image.Image) -> Array:
        with self._lock:
            if self._session is None:
                runtime = import_module("onnxruntime")
                options_factory = cast(Callable[[], _Options], runtime.SessionOptions)
                session_factory = cast(Callable[..., _Session], runtime.InferenceSession)
                options = options_factory()
                options.intra_op_num_threads = 1
                options.inter_op_num_threads = 1
                self._session = session_factory(
                    str(self.weights_path), sess_options=options, providers=["CPUExecutionProvider"]
                )
            outputs = self._session.run(None, {self._session.get_inputs()[0].name: normalize(image)})
            return output_mask(outputs[0], image.size)
