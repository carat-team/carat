import io
import struct
import zlib
from typing import Any

import cv2
import numpy as np
import pytest
from PIL import Image

from carat_algorithms.core import CardPhoto, CheckResult, CheckStatus, ProductCard, get_checks


def make_photo(kind: str) -> CardPhoto:
    height, width = (120, 160) if kind == "small" else (1080, 1920)
    if kind in ("good", "small"):
        rng = np.random.default_rng(0)
        cells = rng.choice([50, 200], size=(height // 3 + 1, width // 3 + 1)).astype(np.uint8)
        image: np.ndarray[Any, Any] = cv2.resize(cells, (width, height), interpolation=cv2.INTER_NEAREST)
    else:
        image = np.full((height, width), 8 if kind == "dark" else 255, dtype=np.uint8)
    stream = io.BytesIO()
    Image.fromarray(image).save(stream, format="PNG")
    return CardPhoto(content=stream.getvalue(), perspective="front")


def run_quality(photos: tuple[CardPhoto, ...]) -> CheckResult:
    check = next((item for item in get_checks() if item.check_id == "image_quality"), None)
    assert check is not None, "Image quality check must run through the shared registry"
    return check.run(ProductCard(photos=photos))


def test_missing_photos_are_not_checked() -> None:
    assert run_quality(()).status == CheckStatus.NOT_CHECKED


@pytest.mark.parametrize(
    "kind,status",
    [
        ("good", CheckStatus.PASS),
        ("small", CheckStatus.WARNING),
        ("dark", CheckStatus.WARNING),
        ("white", CheckStatus.WARNING),
    ],
)
def test_photo_quality(kind: str, status: CheckStatus) -> None:
    result = run_quality((make_photo(kind),))
    assert result.status == status
    assert result.field_refs == ("photos",)
    assert result.algorithm_version == 3
    assert result.reason_code
    assert result.explanation


def test_corrupt_photo_needs_review() -> None:
    result = run_quality((CardPhoto(content=b"invalid"),))
    assert result.status == CheckStatus.REVIEW
    assert result.reason_code == "IMAGE_QUALITY_INVALID_PHOTO"


def test_good_photo_does_not_hide_bad_photo() -> None:
    assert run_quality((make_photo("good"), make_photo("dark"))).status == CheckStatus.WARNING


def test_good_photo_does_not_hide_unreadable_photo() -> None:
    assert run_quality((make_photo("good"), CardPhoto(content=b"invalid"))).status == CheckStatus.REVIEW


def test_moderate_blur_uses_original_runtime_thresholds() -> None:
    photo = make_photo("good")
    with Image.open(io.BytesIO(photo.content)) as image:
        pixels = cv2.GaussianBlur(np.asarray(image), (0, 0), 3.0)
    stream = io.BytesIO()
    Image.fromarray(pixels).save(stream, format="PNG")
    result = run_quality((CardPhoto(content=stream.getvalue()),))
    assert result.status == CheckStatus.REVIEW


def test_malformed_apng_needs_review_instead_of_crashing() -> None:
    stream = io.BytesIO()
    Image.new("RGB", (20, 20), "white").save(stream, format="PNG")
    png = stream.getvalue()
    frame = b"fcTL" + struct.pack(">IIIIIHHBB", 42, 20, 20, 0, 0, 1, 10, 0, 0)
    invalid = png[:-12] + struct.pack(">I", len(frame) - 4) + frame + struct.pack(">I", zlib.crc32(frame)) + png[-12:]
    result = run_quality((CardPhoto(content=invalid),))
    assert result.status == CheckStatus.REVIEW
    assert result.reason_code == "IMAGE_QUALITY_INVALID_PHOTO"
