"""GS1 length and check-digit rules for retail barcodes and the Chestny Znak DataMatrix code.

Ported from BarcodeValidator.java (PR #21, tag legacy/java-backend).
"""

from dataclasses import dataclass
from enum import StrEnum

GTIN_LENGTH = 14
GTIN_LENGTHS = frozenset({8, 12, 13, 14})
# Chestny Znak code: "01" + GTIN-14 + "21" + serial number + optional fields
CHESTNY_ZNAK_GTIN_PREFIX = "01"
CHESTNY_ZNAK_SERIAL_PREFIX = "21"


class CodeFormat(StrEnum):
    EAN_13 = "EAN_13"
    EAN_8 = "EAN_8"
    UPC_A = "UPC_A"
    UPC_E = "UPC_E"
    ITF = "ITF"
    DATA_MATRIX = "DATA_MATRIX"
    OTHER = "OTHER"


@dataclass(frozen=True)
class CodeProblem:
    reason: str
    explanation: str


EMPTY = CodeProblem("EMPTY", "Код пустой")
NOT_DIGITS = CodeProblem("NOT_DIGITS", "Код должен состоять только из цифр")
WRONG_CHECK_DIGIT = CodeProblem("WRONG_CHECK_DIGIT", "Неверная контрольная цифра")
ODD_ITF_LENGTH = CodeProblem("ODD_ITF_LENGTH", "Код ITF должен содержать чётное число цифр")
NOT_CHESTNY_ZNAK = CodeProblem("NOT_CHESTNY_ZNAK", "Это не код Честного Знака: ожидается 01<GTIN>21<серийный номер>")
EMPTY_SERIAL = CodeProblem("EMPTY_SERIAL", "Пустой серийный номер")


def validate_code(text: str, code_format: CodeFormat) -> CodeProblem | None:
    """Validate a decoded barcode. Returns None when the code is valid."""
    if not text:
        return EMPTY
    match code_format:
        case CodeFormat.EAN_13:
            return _validate_gs1_number(text, 13)
        case CodeFormat.EAN_8:
            return _validate_gs1_number(text, 8)
        case CodeFormat.UPC_A:
            return _validate_gs1_number(text, 12)
        case CodeFormat.UPC_E:
            # The UPC-E check digit is calculated over the code expanded to UPC-A
            if _is_digits(text) and len(text) == 8:
                return _validate_gs1_number(_expand_upce(text), 12)
            return _validate_gs1_number(text, 8)
        case CodeFormat.ITF:
            return _validate_itf(text)
        case CodeFormat.DATA_MATRIX:
            return _validate_chestny_znak(text)
        case CodeFormat.OTHER:
            return None


def validate_gtin(text: str) -> CodeProblem | None:
    """Validate a GTIN typed into a card: GTIN-8, GTIN-12, GTIN-13 or GTIN-14."""
    if not text:
        return EMPTY
    if not _is_digits(text):
        return NOT_DIGITS
    if len(text) not in GTIN_LENGTHS:
        return CodeProblem("WRONG_LENGTH", f"Ожидается 8, 12, 13 или 14 цифр, получено {len(text)}")
    if not _has_valid_check_digit(text):
        return WRONG_CHECK_DIGIT
    return None


def _validate_gs1_number(text: str, length: int) -> CodeProblem | None:
    if not _is_digits(text):
        return NOT_DIGITS
    if len(text) != length:
        return CodeProblem("WRONG_LENGTH", f"Ожидается {length} цифр, получено {len(text)}")
    if not _has_valid_check_digit(text):
        return WRONG_CHECK_DIGIT
    return None


def _validate_itf(text: str) -> CodeProblem | None:
    if not _is_digits(text):
        return NOT_DIGITS
    if len(text) % 2 != 0:
        return ODD_ITF_LENGTH
    # ITF-14 is a GTIN, shorter ITF codes have no check digit
    if len(text) == GTIN_LENGTH and not _has_valid_check_digit(text):
        return WRONG_CHECK_DIGIT
    return None


def _validate_chestny_znak(text: str) -> CodeProblem | None:
    serial_start = len(CHESTNY_ZNAK_GTIN_PREFIX) + GTIN_LENGTH
    has_structure = text.startswith(CHESTNY_ZNAK_GTIN_PREFIX) and text.startswith(
        CHESTNY_ZNAK_SERIAL_PREFIX, serial_start
    )
    if not has_structure:
        return NOT_CHESTNY_ZNAK
    if len(text) == serial_start + len(CHESTNY_ZNAK_SERIAL_PREFIX):
        return EMPTY_SERIAL
    return _validate_gs1_number(text[len(CHESTNY_ZNAK_GTIN_PREFIX) : serial_start], GTIN_LENGTH)


def _expand_upce(text: str) -> str:
    """Expand an 8-digit UPC-E code to UPC-A, same table as ZXing's UPCEReader.convertUPCEtoUPCA."""
    digits = text[1:7]
    last = digits[5]
    if last in "012":
        middle = digits[0:2] + last + "0000" + digits[2:5]
    elif last == "3":
        middle = digits[0:3] + "00000" + digits[3:5]
    elif last == "4":
        middle = digits[0:4] + "00000" + digits[4]
    else:
        middle = digits[0:5] + "0000" + last
    return text[0] + middle + text[7]


def _is_digits(text: str) -> bool:
    # str.isdigit() also accepts superscripts and other Unicode digits
    return all("0" <= char <= "9" for char in text)


def _has_valid_check_digit(digits: str) -> bool:
    # GS1: weights 3 and 1 alternate from the rightmost digit before the check digit
    total = sum(int(digit) * (3 if index % 2 == 0 else 1) for index, digit in enumerate(reversed(digits[:-1])))
    return (10 - total % 10) % 10 == int(digits[-1])
