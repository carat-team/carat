import pytest

from carat_algorithms.identifiers.gtin import CodeFormat, validate_code, validate_gtin

# Every case from BarcodeValidatorTest.java (tag legacy/java-backend); None means the code is valid
VALIDATE_CODE_CASES = [
    pytest.param("3614272049529", CodeFormat.EAN_13, None, id="ean13-valid"),
    pytest.param("96385074", CodeFormat.EAN_8, None, id="ean8-valid"),
    pytest.param("036000291452", CodeFormat.UPC_A, None, id="upca-valid"),
    pytest.param("3614272049520", CodeFormat.EAN_13, "WRONG_CHECK_DIGIT", id="ean13-wrong-check-digit"),
    pytest.param("361427204952", CodeFormat.EAN_13, "WRONG_LENGTH", id="ean13-too-short"),
    pytest.param("36142720495A9", CodeFormat.EAN_13, "NOT_DIGITS", id="ean13-letter"),
    pytest.param("04252614", CodeFormat.UPC_E, None, id="upce-valid-over-expanded-upca"),
    pytest.param("04252610", CodeFormat.UPC_E, "WRONG_CHECK_DIGIT", id="upce-wrong-check-digit"),
    pytest.param("0425261", CodeFormat.UPC_E, "WRONG_LENGTH", id="upce-too-short"),
    pytest.param("8603095259", CodeFormat.ITF, None, id="itf-short-without-check-digit"),
    pytest.param("14601234567890", CodeFormat.ITF, None, id="itf14-valid"),
    pytest.param("12345", CodeFormat.ITF, "ODD_ITF_LENGTH", id="itf-odd-length"),
    pytest.param("14601234567891", CodeFormat.ITF, "WRONG_CHECK_DIGIT", id="itf14-wrong-check-digit"),
    pytest.param("0104600439931256215Q8H6t\x1d93abcd", CodeFormat.DATA_MATRIX, None, id="chestny-znak-valid"),
    pytest.param("0104600439931257215Q8H6t", CodeFormat.DATA_MATRIX, "WRONG_CHECK_DIGIT", id="chestny-znak-bad-gtin"),
    pytest.param("010460043993125621", CodeFormat.DATA_MATRIX, "EMPTY_SERIAL", id="chestny-znak-empty-serial"),
    pytest.param("hello", CodeFormat.DATA_MATRIX, "NOT_CHESTNY_ZNAK", id="chestny-znak-wrong-structure"),
    pytest.param("https://example.com", CodeFormat.OTHER, None, id="other-format-any-text"),
    pytest.param("", CodeFormat.OTHER, "EMPTY", id="other-format-empty"),
]


@pytest.mark.parametrize(("text", "code_format", "expected_reason"), VALIDATE_CODE_CASES)
def test_validate_code(text: str, code_format: CodeFormat, expected_reason: str | None) -> None:
    problem = validate_code(text, code_format)

    assert (problem.reason if problem else None) == expected_reason


def test_wrong_length_names_expected_and_actual_length() -> None:
    problem = validate_code("361427204952", CodeFormat.EAN_13)

    assert problem is not None
    assert problem.explanation == "Ожидается 13 цифр, получено 12"


@pytest.mark.parametrize(
    ("text", "expected_reason"),
    [
        pytest.param("96385074", None, id="gtin8"),
        pytest.param("036000291452", None, id="gtin12"),
        pytest.param("3614272049529", None, id="gtin13"),
        pytest.param("04600439931256", None, id="gtin14"),
        pytest.param("3614272049520", "WRONG_CHECK_DIGIT", id="wrong-check-digit"),
        pytest.param("3614272049", "WRONG_LENGTH", id="ten-digits"),
        pytest.param("36142720495A9", "NOT_DIGITS", id="letter"),
        pytest.param(" 3614272049529", "NOT_DIGITS", id="leading-space"),
        pytest.param("361427204952٩", "NOT_DIGITS", id="non-ascii-digit"),
        pytest.param("", "EMPTY", id="empty"),
    ],
)
def test_validate_gtin(text: str, expected_reason: str | None) -> None:
    problem = validate_gtin(text)

    assert (problem.reason if problem else None) == expected_reason
