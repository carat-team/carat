import io
import sys
from pathlib import Path

import pytest

from carat_algorithms.vision.ocr import OcrReader, TextBlock, downscaled_size


@pytest.mark.parametrize(
    ("size", "expected"),
    [
        pytest.param((2000, 1000), (1600, 800), id="landscape-downscaled"),
        pytest.param((1000, 3000), (533, 1600), id="portrait-downscaled-and-rounded"),
        pytest.param((800, 600), (800, 600), id="small-kept"),
        pytest.param((1600, 1600), (1600, 1600), id="exact-limit-kept"),
    ],
)
def test_downscaled_size(size: tuple[int, int], expected: tuple[int, int]) -> None:
    assert downscaled_size(*size, max_side=1600) == expected


def test_creating_a_reader_does_not_load_the_model(tmp_path: Path) -> None:
    reader = OcrReader(tmp_path)

    assert "easyocr" not in sys.modules
    assert reader.weights_directory == tmp_path / "easyocr"


class FakeEasyOcr:
    def __init__(self) -> None:
        self.image: object = None

    def readtext(self, image: object) -> list[tuple[object, str, float]]:
        self.image = image
        return [(None, "Eau de Parfum", 0.9), (None, "шум", 0.1)]


def test_read_text_downscales_and_drops_low_confidence(tmp_path: Path) -> None:
    numpy = pytest.importorskip("numpy")  # comes with the ml extra
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (3200, 1000)).save(buffer, "PNG")
    fake = FakeEasyOcr()
    reader = OcrReader(tmp_path)
    reader._reader = fake  # pyright: ignore[reportPrivateUsage]

    assert reader.read_text(buffer.getvalue()) == [TextBlock("Eau de Parfum", 0.9)]
    assert numpy.asarray(fake.image).shape == (500, 1600, 3)
