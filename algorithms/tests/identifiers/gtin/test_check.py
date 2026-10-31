import pytest

from carat_algorithms.core import CheckStatus, ProductCard
from carat_algorithms.identifiers.gtin import GtinFormatCheck


@pytest.mark.parametrize(
    ("gtin", "expected_status", "expected_reason_code"),
    [
        pytest.param(None, CheckStatus.NOT_CHECKED, "GTIN_FORMAT_MISSING", id="absent"),
        pytest.param("", CheckStatus.WARNING, "GTIN_FORMAT_EMPTY", id="empty-string-is-a-finding"),
        pytest.param("3614272049529", CheckStatus.PASS, "GTIN_FORMAT_OK", id="gtin13"),
        pytest.param("04600439931256", CheckStatus.PASS, "GTIN_FORMAT_OK", id="gtin14"),
        pytest.param("3614272049520", CheckStatus.WARNING, "GTIN_FORMAT_WRONG_CHECK_DIGIT", id="wrong-check-digit"),
        pytest.param("36142720495A9", CheckStatus.WARNING, "GTIN_FORMAT_NOT_DIGITS", id="letter"),
        pytest.param("3614272049", CheckStatus.WARNING, "GTIN_FORMAT_WRONG_LENGTH", id="ten-digits"),
    ],
)
def test_gtin_format(gtin: str | None, expected_status: CheckStatus, expected_reason_code: str) -> None:
    result = GtinFormatCheck().run(ProductCard(gtin=gtin))

    assert result.status is expected_status
    assert result.reason_code == expected_reason_code
    assert result.field_refs == ("gtin",)
    assert result.algorithm_version == 1


def test_explanation_names_the_gtin_and_the_problem() -> None:
    result = GtinFormatCheck().run(ProductCard(gtin="3614272049520"))

    assert result.explanation == "GTIN 3614272049520: Неверная контрольная цифра"
