import io
from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from PIL.PngImagePlugin import PngInfo

from carat_algorithms.core import CardPhoto, CheckStatus, ProductCard, get_checks
from carat_algorithms.vision.image_origin import ImageOriginCheck
from carat_algorithms.vision.image_origin.detector import (
    GENERATION_LOGIT,
    WEIGHTS_FILENAME,
    WEIGHTS_SUBDIRECTORY,
    PixelDetector,
    UnsupportedPhotoError,
    preprocess,
)


def _photo(fmt: str = "PNG", *, labelled: bool = False, size: tuple[int, int] = (512, 400)) -> CardPhoto:
    stream = io.BytesIO()
    with Image.new("RGB", size, (95, 155, 210)) as image:
        if labelled:
            tags = PngInfo()
            tags.add_itxt("XML:com.adobe.xmp", "AI-generated")
            image.save(stream, format=fmt, pnginfo=tags)
        else:
            image.save(stream, format=fmt)
    return CardPhoto(content=stream.getvalue())


@pytest.fixture
def weights_dir(tmp_path: Path) -> Path:
    path = tmp_path / WEIGHTS_SUBDIRECTORY / WEIGHTS_FILENAME
    path.parent.mkdir()
    path.touch()
    return tmp_path


def test_registered_check_with_no_photos() -> None:
    check = next(check for check in get_checks() if check.check_id == "image_origin")
    assert check.run(ProductCard()).reason_code == "IMAGE_ORIGIN_NO_PHOTOS"


def test_missing_weights_do_not_start_model(tmp_path: Path) -> None:
    result = ImageOriginCheck(tmp_path).run(ProductCard(photos=(_photo(),)))
    assert (result.status, result.reason_code) == (CheckStatus.NOT_CHECKED, "IMAGE_ORIGIN_WEIGHTS_MISSING")


@pytest.mark.parametrize("fmt", ["JPEG", "PNG", "WEBP"])
def test_supported_image_formats_have_right_input(fmt: str) -> None:
    tensor = preprocess(_photo(fmt).content)
    assert tensor.shape == (1, 3, 384, 384)
    assert tensor.dtype == np.float32 and tensor.flags.c_contiguous
    np.testing.assert_allclose(tensor[0, 0], (95 / 255 - 0.485) / 0.229, atol=0.03)


def test_provenance_metadata_does_not_change_model_input() -> None:
    np.testing.assert_array_equal(preprocess(_photo().content), preprocess(_photo(labelled=True).content))


@pytest.mark.parametrize("size", [(32, 32), (224, 1793), (4000, 3001)])
def test_rejects_out_of_scope_sizes(size: tuple[int, int]) -> None:
    with pytest.raises(UnsupportedPhotoError):
        preprocess(_photo(size=size).content)


def test_strong_signal_after_an_unreadable_photo(weights_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def score(_detector: PixelDetector, content: bytes) -> float:
        if not content:
            raise UnsupportedPhotoError("empty")
        return GENERATION_LOGIT

    monkeypatch.setattr(PixelDetector, "score", score)
    check = next(check for check in get_checks(weights_dir) if check.check_id == "image_origin")
    result = check.run(ProductCard(photos=(CardPhoto(content=b""), _photo())))
    assert (result.status, result.reason_code) == (CheckStatus.WARNING, "IMAGE_ORIGIN_AI_SIGNAL")
    assert "Фото 2" in result.explanation
    assert result.field_refs == ("photos",)


def test_low_score_requires_review(weights_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def score(_detector: PixelDetector, _content: bytes) -> float:
        return GENERATION_LOGIT - 0.01

    monkeypatch.setattr(PixelDetector, "score", score)
    result = ImageOriginCheck(weights_dir).run(ProductCard(photos=(_photo(),)))
    assert (result.status, result.reason_code) == (CheckStatus.REVIEW, "IMAGE_ORIGIN_INCONCLUSIVE")


def test_corrupt_photo_requires_review(weights_dir: Path) -> None:
    result = ImageOriginCheck(weights_dir).run(ProductCard(photos=(CardPhoto(content=b"broken"),)))
    assert (result.status, result.reason_code) == (CheckStatus.REVIEW, "IMAGE_ORIGIN_UNSUPPORTED_PHOTO")


def test_corrupt_weights_are_an_operational_error(weights_dir: Path) -> None:
    with pytest.raises(RuntimeError, match="model size"):
        ImageOriginCheck(weights_dir).run(ProductCard(photos=(_photo(),)))
