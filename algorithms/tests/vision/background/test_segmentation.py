from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest
from PIL import Image

from carat_algorithms.vision.background import segmentation


def test_normalization_matches_rembg_channels_and_scale() -> None:
    result = segmentation.normalize(Image.new("RGB", (32, 16), (200, 100, 0)))
    assert result.shape == (1, 3, 1024, 1024)
    assert result.dtype == np.float32
    np.testing.assert_allclose(result[0, :, 0, 0], [0.5, 0, -0.5])


def test_black_image_normalization_is_finite() -> None:
    result = segmentation.normalize(Image.new("RGB", (8, 8)))
    assert np.isfinite(result).all() and np.all(result == -0.5)


def test_output_mask_is_scaled_and_resized() -> None:
    values = np.array([[[[2, 4], [2, 4]]]], dtype=np.float32)
    result = segmentation.output_mask(values, (20, 10))
    assert result.shape == (10, 20) and result.dtype == np.uint8
    assert result.min() == 0 and result.max() == 255


def test_constant_output_is_an_empty_mask_without_nan() -> None:
    result = segmentation.output_mask(np.ones((1, 1, 4, 4)), (20, 10))
    assert not result.any()


@pytest.mark.parametrize("output", [np.zeros((2, 2)), np.zeros((1, 1, 0, 0)), np.full((1, 1, 2, 2), np.nan)])
def test_invalid_model_output_is_rejected(output: np.ndarray[Any, Any]) -> None:
    with pytest.raises(ValueError):
        segmentation.output_mask(output, (20, 10))


def test_session_loads_lazily_once_from_local_weights(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    class Session:
        def get_inputs(self) -> list[SimpleNamespace]:
            return [SimpleNamespace(name="image")]

        def run(self, output_names: None, input_feed: dict[str, np.ndarray[Any, Any]]) -> list[np.ndarray[Any, Any]]:
            assert input_feed["image"].shape == (1, 3, 1024, 1024)
            return [np.array([[[[0, 1], [0, 1]]]], dtype=np.float32)]

    def create_session(path: str, **kwargs: object) -> Session:
        calls.append((path, kwargs))
        return Session()

    runtime = SimpleNamespace(SessionOptions=SimpleNamespace, InferenceSession=create_session)

    def import_runtime(name: str) -> SimpleNamespace:
        assert name == "onnxruntime"
        return runtime

    monkeypatch.setattr(segmentation, "import_module", import_runtime)
    segmenter = segmentation.ISNetSegmenter(tmp_path)
    assert not calls
    for _ in range(2):
        assert segmenter.segment(Image.new("RGB", (20, 10))).shape == (10, 20)
    assert len(calls) == 1
    assert Path(calls[0][0]) == tmp_path / "isnet" / "isnet-general-use.onnx"
    assert calls[0][1]["providers"] == ["CPUExecutionProvider"]
