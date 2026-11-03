import io
import struct
from typing import Any

import cv2
import numpy as np
import pytest
from PIL import Image, ImageOps

from carat_algorithms.core import CardPhoto, CheckStatus, ProductCard
from carat_algorithms.vision.quality import ImageQualityCheck, analysis


def encode(image: Image.Image) -> CardPhoto:
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    return CardPhoto(content=stream.getvalue())


def good_image(size: tuple[int, int] = (1920, 1080)) -> Image.Image:
    rng = np.random.default_rng(7)
    pixels = rng.choice([50, 200], size=(size[1] // 6 + 1, size[0] // 6 + 1)).astype(np.uint8)
    pixels = cv2.resize(pixels, size, interpolation=cv2.INTER_NEAREST)
    return Image.fromarray(pixels).convert("RGB")


def test_hidden_rgb_under_transparency_does_not_change_quality() -> None:
    base = np.asarray(good_image((1200, 1200))).copy()
    alpha = np.zeros((1200, 1200), dtype=np.uint8)
    alpha[500:700, 500:700] = 255
    images: list[CardPhoto] = []
    for hidden in (0, 255):
        rgb = base.copy()
        rgb[alpha == 0] = hidden
        images.append(encode(Image.fromarray(np.dstack((rgb, alpha)))))
    check = ImageQualityCheck()
    dark_hidden = check.run(ProductCard(photos=(images[0],)))
    white_hidden = check.run(ProductCard(photos=(images[1],)))
    assert dark_hidden == white_hidden


def test_large_transparent_photo_is_bounded_before_compositing(monkeypatch: pytest.MonkeyPatch) -> None:
    composite = Image.alpha_composite
    observed: list[tuple[int, int]] = []

    def bounded(background: Image.Image, foreground: Image.Image) -> Image.Image:
        observed.append(foreground.size)
        assert max(foreground.size) <= 1024, "Avoid full-size RGBA intermediate buffers"
        return composite(background, foreground)

    monkeypatch.setattr(Image, "alpha_composite", bounded)
    result = ImageQualityCheck().run(ProductCard(photos=(encode(good_image((3200, 1600)).convert("RGBA")),)))
    assert observed and result.status != CheckStatus.ERROR


def test_analysis_resolution_can_use_original_dimensions() -> None:
    small = np.asarray(good_image((512, 288)))
    result = analysis.analyze_quality(small, original_size=(3840, 2160))
    assert (result.width, result.height) == (3840, 2160)
    assert result.resolution == 100


def test_check_keeps_original_dimensions_after_downscale_and_orientation(monkeypatch: pytest.MonkeyPatch) -> None:
    analyze = analysis.analyze_quality
    seen: list[tuple[int, int]] = []

    def capture(
        image: np.ndarray[Any, Any],
        config: analysis.QualityConfig | None = None,
        *,
        original_size: tuple[int, int] | None = None,
    ) -> analysis.QualityResult:
        assert max(image.shape[:2]) <= 1024
        result = analyze(image, config, original_size=original_size)
        seen.append((result.width, result.height))
        return result

    monkeypatch.setattr(analysis, "analyze_quality", capture)
    stream = io.BytesIO()
    exif = Image.Exif()
    exif[274] = 6
    good_image((3200, 1600)).save(stream, format="JPEG", exif=exif)
    ImageQualityCheck().run(ProductCard(photos=(CardPhoto(content=stream.getvalue()),)))
    assert seen == [(1600, 3200)]


@pytest.mark.parametrize("error", [TypeError("bad EXIF"), struct.error("bad EXIF"), ZeroDivisionError("bad rational")])
def test_malformed_metadata_needs_review_and_next_photo_runs(error: Exception, monkeypatch: pytest.MonkeyPatch) -> None:
    transpose = ImageOps.exif_transpose
    calls = 0

    def exif(image: Image.Image) -> Image.Image:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise error
        return transpose(image)

    monkeypatch.setattr(ImageOps, "exif_transpose", exif)
    photo = encode(good_image())
    result = ImageQualityCheck().run(ProductCard(photos=(photo, photo)))
    assert calls == 2
    assert result.status == CheckStatus.REVIEW and result.reason_code == "IMAGE_QUALITY_INVALID_PHOTO"


def test_cv_decoder_analysis_error_does_not_abort_remaining_photos(monkeypatch: pytest.MonkeyPatch) -> None:
    analyze = analysis.analyze_quality
    calls = 0

    def failing_first(
        image: np.ndarray[Any, Any],
        config: analysis.QualityConfig | None = None,
        *,
        original_size: tuple[int, int] | None = None,
    ) -> analysis.QualityResult:
        nonlocal calls
        calls += 1
        if calls == 1:
            error = cv2.error("unsupported image")
            error.code = cv2.Error.StsUnsupportedFormat
            raise error
        return analyze(image, config, original_size=original_size)

    monkeypatch.setattr(analysis, "analyze_quality", failing_first)
    photo = encode(good_image())
    result = ImageQualityCheck().run(ProductCard(photos=(photo, photo)))
    assert calls == 2 and result.status == CheckStatus.REVIEW


def test_unexpected_analysis_failure_is_left_for_runner(monkeypatch: pytest.MonkeyPatch) -> None:
    def failed(*args: object, **kwargs: object) -> analysis.QualityResult:
        raise RuntimeError("programming failure")

    monkeypatch.setattr(analysis, "analyze_quality", failed)
    with pytest.raises(RuntimeError, match="programming failure"):
        ImageQualityCheck().run(ProductCard(photos=(encode(good_image()),)))


def test_quality_explanation_includes_photo_dimensions_and_measurement() -> None:
    result = ImageQualityCheck().run(ProductCard(photos=(encode(Image.new("RGB", (320, 200), (8, 8, 8))),)))
    assert "Фото 1" in result.explanation and "320x200" in result.explanation
    assert "8" in result.explanation and "120" in result.explanation


@pytest.mark.parametrize("mode", ["P", "1"])
def test_palette_and_binary_png_match_identical_rgb_pixels(mode: str) -> None:
    rng = np.random.default_rng(0)
    values = [100, 140] if mode == "P" else [0, 255]
    pixels = rng.choice(values, size=(2048, 2048)).astype(np.uint8)
    indexed = Image.fromarray(pixels).convert(mode)
    rgb = indexed.convert("RGB")
    check = ImageQualityCheck()
    result_rgb = check.run(ProductCard(photos=(encode(rgb),)))
    result_indexed = check.run(ProductCard(photos=(encode(indexed),)))
    assert result_indexed == result_rgb


@pytest.mark.parametrize("code", [cv2.Error.StsNoMem, cv2.Error.StsInternal, cv2.Error.StsError])
def test_cv_resource_and_internal_failures_are_left_for_runner(code: int, monkeypatch: pytest.MonkeyPatch) -> None:
    error = cv2.error("runtime failure")
    error.code = code

    def failed(*args: object, **kwargs: object) -> analysis.QualityResult:
        raise error

    monkeypatch.setattr(analysis, "analyze_quality", failed)
    with pytest.raises(cv2.error):
        ImageQualityCheck().run(ProductCard(photos=(encode(good_image()),)))


@pytest.mark.parametrize("mode", ["RGB", "L"])
def test_png_color_key_transparency_matches_explicit_rgba(mode: str, monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[np.ndarray[Any, Any]] = []
    analyze = analysis.analyze_quality

    def capture(
        image: np.ndarray[Any, Any],
        config: analysis.QualityConfig | None = None,
        *,
        original_size: tuple[int, int] | None = None,
    ) -> analysis.QualityResult:
        seen.append(image.copy())
        return analyze(image, config, original_size=original_size)

    monkeypatch.setattr(analysis, "analyze_quality", capture)
    pixels = np.zeros((2048, 2048, 3) if mode == "RGB" else (2048, 2048), dtype=np.uint8)
    key = (255, 0, 255) if mode == "RGB" else 200
    pixels[:, ::2] = key
    source = Image.fromarray(pixels)
    source.info["transparency"] = key
    reference = source.convert("RGBA")
    check = ImageQualityCheck()
    for image in (source, reference):
        check.run(ProductCard(photos=(encode(image),)))
    np.testing.assert_array_equal(seen[0], seen[1])


def test_valid_sixteen_bit_grayscale_png_is_decoded() -> None:
    image = Image.new("I;16", (2048, 1024), 16384)
    result = ImageQualityCheck().run(ProductCard(photos=(encode(image),)))
    assert result.reason_code != "IMAGE_QUALITY_INVALID_PHOTO"
