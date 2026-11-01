from collections.abc import Callable

import pytest

pytest.importorskip("zxingcpp")

from carat_algorithms.core import CardPhoto, CheckStatus, ProductCard  # noqa: E402
from carat_algorithms.vision.barcode import BarcodeOnPhotoCheck  # noqa: E402

RenderBarcode = Callable[..., bytes]


def run_on(*photos: bytes) -> tuple[CheckStatus, str, str]:
    result = BarcodeOnPhotoCheck().run(ProductCard(photos=tuple(CardPhoto(content=photo) for photo in photos)))
    assert result.field_refs == ("photos",)
    return result.status, result.reason_code, result.explanation


def test_no_photos_is_not_checked() -> None:
    assert run_on()[:2] == (CheckStatus.NOT_CHECKED, "BARCODE_ON_PHOTO_NO_PHOTOS")


def test_unreadable_photo_needs_review() -> None:
    assert run_on(b"not an image")[:2] == (CheckStatus.REVIEW, "BARCODE_ON_PHOTO_UNREADABLE")


def test_photo_without_code_needs_review(blank_png: bytes) -> None:
    assert run_on(blank_png)[:2] == (CheckStatus.REVIEW, "BARCODE_ON_PHOTO_NOT_FOUND")


def test_valid_codes_pass(render_barcode: RenderBarcode, blank_png: bytes) -> None:
    status, reason_code, explanation = run_on(
        blank_png, render_barcode("3614272049529", "EAN13"), render_barcode("0104600439931256215Q8H6t", "DataMatrix")
    )

    assert (status, reason_code) == (CheckStatus.PASS, "BARCODE_ON_PHOTO_OK")
    assert explanation == "Найдено кодов на фото: 2, все корректны"


def test_invalid_chestny_znak_code_is_a_warning(render_barcode: RenderBarcode) -> None:
    status, reason_code, explanation = run_on(render_barcode("hello", "DataMatrix"))

    assert (status, reason_code) == (CheckStatus.WARNING, "BARCODE_ON_PHOTO_INVALID_CODE")
    assert explanation.startswith("Код DATA_MATRIX на фото: Это не код Честного Знака")


def test_same_code_on_two_photos_counts_once(render_barcode: RenderBarcode) -> None:
    ean13 = render_barcode("3614272049529", "EAN13")

    assert run_on(ean13, ean13)[2] == "Найдено кодов на фото: 1, все корректны"
