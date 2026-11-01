from collections.abc import Callable

import pytest

pytest.importorskip("zxingcpp")

from carat_algorithms.identifiers.gtin import CodeFormat  # noqa: E402
from carat_algorithms.vision.barcode import DecodedCode, read_codes  # noqa: E402

RenderBarcode = Callable[..., bytes]


def test_reads_ean13(render_barcode: RenderBarcode) -> None:
    image = render_barcode("3614272049529", "EAN13")

    assert read_codes(image) == [DecodedCode("3614272049529", CodeFormat.EAN_13)]


def test_reads_data_matrix(render_barcode: RenderBarcode) -> None:
    image = render_barcode("0104600439931256215Q8H6t", "DataMatrix")

    assert read_codes(image) == [DecodedCode("0104600439931256215Q8H6t", CodeFormat.DATA_MATRIX)]


def test_reads_gs1_data_matrix_with_group_separator(render_barcode: RenderBarcode) -> None:
    image = render_barcode("(01)04600439931256(21)5Q8H6t(93)abcd", "DataMatrix", gs1=True)

    assert read_codes(image) == [DecodedCode("0104600439931256215Q8H6t\x1d93abcd", CodeFormat.DATA_MATRIX)]


def test_reads_upce_as_eight_digits(render_barcode: RenderBarcode) -> None:
    image = render_barcode("04252614", "UPCE")

    assert read_codes(image) == [DecodedCode("04252614", CodeFormat.UPC_E)]


def test_returns_empty_list_when_no_code(blank_png: bytes) -> None:
    assert read_codes(blank_png) == []


def test_returns_none_for_bytes_that_are_not_an_image() -> None:
    assert read_codes(b"not an image") is None
