import io
import struct
from typing import Any

import numpy as np
import pytest
from PIL import Image, ImageOps

from carat_algorithms.core import CardPhoto, CheckStatus, ProductCard
from carat_algorithms.vision.background import BackgroundCheck


class EmptySegmenter:
    def segment(self, image: Image.Image) -> np.ndarray[Any, Any]:
        return np.zeros((image.height, image.width), dtype=np.uint8)


def encode(image: Image.Image) -> CardPhoto:
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    return CardPhoto(content=stream.getvalue())


def test_large_rgba_is_bounded_before_compositing(monkeypatch: pytest.MonkeyPatch) -> None:
    composite = Image.alpha_composite
    observed: list[tuple[int, int]] = []

    def bounded(background: Image.Image, foreground: Image.Image) -> Image.Image:
        observed.append(foreground.size)
        assert max(foreground.size) <= 512, "Avoid full-size RGBA intermediate buffers"
        return composite(background, foreground)

    monkeypatch.setattr(Image, "alpha_composite", bounded)
    result = BackgroundCheck(segmenter=EmptySegmenter()).run(
        ProductCard(photos=(encode(Image.new("RGBA", (3200, 1600))),))
    )
    assert observed and result.reason_code == "BACKGROUND_NO_OBJECT"


@pytest.mark.parametrize("error", [TypeError("bad EXIF"), struct.error("bad EXIF"), ZeroDivisionError("bad rational")])
def test_malformed_metadata_needs_review(error: Exception, monkeypatch: pytest.MonkeyPatch) -> None:
    def failed(image: Image.Image) -> Image.Image:
        raise error

    monkeypatch.setattr(ImageOps, "exif_transpose", failed)
    result = BackgroundCheck(segmenter=EmptySegmenter()).run(ProductCard(photos=(encode(Image.new("RGB", (20, 20))),)))
    assert result.status == CheckStatus.REVIEW and result.reason_code == "BACKGROUND_INVALID_PHOTO"


def test_worst_finding_identifies_its_photo() -> None:
    class Segmenter:
        def segment(self, image: Image.Image) -> np.ndarray[Any, Any]:
            mask = np.zeros((image.height, image.width), dtype=np.uint8)
            mask[40:160, 30:80] = 255
            return mask

    image = np.full((200, 200, 3), 240, dtype=np.uint8)
    image[40:160, 30:80] = 0
    bad = image.copy()
    bad[20:50, 140:170] = (200, 30, 30)
    result = BackgroundCheck(segmenter=Segmenter()).run(
        ProductCard(photos=(encode(Image.fromarray(image)), encode(Image.fromarray(bad))))
    )
    assert result.status == CheckStatus.WARNING
    assert "Фото 2" in result.explanation


def test_unexpected_segmentation_failure_is_left_for_runner() -> None:
    class FailedSegmenter:
        def segment(self, image: Image.Image) -> np.ndarray[Any, Any]:
            raise RuntimeError("invalid installed model")

    with pytest.raises(RuntimeError, match="invalid installed model"):
        BackgroundCheck(segmenter=FailedSegmenter()).run(ProductCard(photos=(encode(Image.new("RGB", (20, 20))),)))


@pytest.mark.parametrize("mode", ["P", "1"])
def test_palette_and_binary_photos_send_identical_pixels_to_model(mode: str) -> None:
    seen: list[np.ndarray[Any, Any]] = []

    class RecordingSegmenter:
        def segment(self, image: Image.Image) -> np.ndarray[Any, Any]:
            seen.append(np.asarray(image).copy())
            return np.zeros((image.height, image.width), dtype=np.uint8)

    values = [100, 140] if mode == "P" else [0, 255]
    pixels = np.random.default_rng(0).choice(values, size=(2048, 2048)).astype(np.uint8)
    indexed = Image.fromarray(pixels).convert(mode)
    check = BackgroundCheck(segmenter=RecordingSegmenter())
    for image in (indexed, indexed.convert("RGB")):
        check.run(ProductCard(photos=(encode(image),)))
    np.testing.assert_array_equal(seen[0], seen[1])


@pytest.mark.parametrize("mode", ["RGB", "L"])
def test_png_color_key_transparency_matches_explicit_rgba(mode: str) -> None:
    seen: list[np.ndarray[Any, Any]] = []

    class RecordingSegmenter:
        def segment(self, image: Image.Image) -> np.ndarray[Any, Any]:
            seen.append(np.asarray(image).copy())
            return np.zeros((image.height, image.width), dtype=np.uint8)

    pixels = np.zeros((1024, 1024, 3) if mode == "RGB" else (1024, 1024), dtype=np.uint8)
    key = (255, 0, 255) if mode == "RGB" else 200
    pixels[:, ::2] = key
    source = Image.fromarray(pixels)
    source.info["transparency"] = key
    reference = source.convert("RGBA")
    check = BackgroundCheck(segmenter=RecordingSegmenter())
    for image in (source, reference):
        check.run(ProductCard(photos=(encode(image),)))
    np.testing.assert_array_equal(seen[0], seen[1])


def test_valid_sixteen_bit_grayscale_png_is_decoded() -> None:
    image = Image.new("I;16", (2048, 1024), 16384)
    result = BackgroundCheck(segmenter=EmptySegmenter()).run(ProductCard(photos=(encode(image),)))
    assert result.reason_code == "BACKGROUND_NO_OBJECT"
