"""Supported units, text patterns, and category profiles."""

import re
from dataclasses import dataclass
from decimal import Decimal

# Names of fields in the current CARAT product-card export.
NAME = "Полное наименование товара (2478)"
VALUE = "Заявленный объем (2716)"
UNIT = "Тип (2716)"

# Spelling -> (physical dimension, conversion factor, canonical unit).
# Mass and volume stay separate because product density is not provided.
UNITS = {
    "мл": ("volume", Decimal(1), "мл"), "ml": ("volume", Decimal(1), "мл"),
    "л": ("volume", Decimal(1000), "мл"), "l": ("volume", Decimal(1000), "мл"),
    "литр": ("volume", Decimal(1000), "мл"),
    "литра": ("volume", Decimal(1000), "мл"),
    "литров": ("volume", Decimal(1000), "мл"),
    "миллилитр": ("volume", Decimal(1), "мл"),
    "миллилитра": ("volume", Decimal(1), "мл"),
    "миллилитров": ("volume", Decimal(1), "мл"),
    "г": ("mass", Decimal(1), "г"), "g": ("mass", Decimal(1), "г"),
    "гр": ("mass", Decimal(1), "г"), "грамм": ("mass", Decimal(1), "г"),
    "грамма": ("mass", Decimal(1), "г"),
    "граммов": ("mass", Decimal(1), "г"),
    "кг": ("mass", Decimal(1000), "г"), "kg": ("mass", Decimal(1000), "г"),
}

UNIT_PATTERN = "|".join(re.escape(unit) for unit in sorted(UNITS, key=len, reverse=True))
NUM = r"\d+(?:[.,]\d+)?"
COUNT = r"\d+"
COUNT_START = rf"(?<![\d.,]){COUNT}"
PIECES = r"(?:шт\.?|штук(?:а|и)?|pcs?|pieces?)"
MULTIPLY = r"[xх×*]"
AMOUNT_TEXT = rf"(?P<value>{NUM})\s*(?P<unit>{UNIT_PATTERN})(?!\w)"

# Blue100ml and Parfum,100 мл are valid; tails of larger numbers are not.
AMOUNT = re.compile(rf"(?<![\d.+])(?<!\d,){AMOUNT_TEXT}", re.I)
SET_TERM = re.compile(
    rf"(?P<per>(?P<per_count>{COUNT_START})\s*{PIECES}\s*(?:по|each)\s*"
    rf"(?P<per_value>{NUM})\s*(?P<per_unit>{UNIT_PATTERN})(?!\w))"
    rf"|(?P<prefix>(?P<prefix_count>{COUNT_START})\s*(?:{PIECES}\s*)?{MULTIPLY}\s*"
    rf"(?P<prefix_value>{NUM})\s*(?P<prefix_unit>{UNIT_PATTERN})(?!\w))"
    rf"|(?P<suffix>(?P<suffix_value>{NUM})\s*(?P<suffix_unit>{UNIT_PATTERN})(?!\w)\s*"
    rf"{MULTIPLY}\s*(?P<suffix_count>{COUNT})(?![.,]\d)(?:\s*{PIECES})?)"
    rf"|(?P<single>(?<![\d.+])(?<!\d,)(?P<single_value>{NUM})\s*"
    rf"(?P<single_unit>{UNIT_PATTERN})(?!\w))", re.I)
SUM_SEPARATOR = re.compile(r"^\s*(?:\+|&|и|and|plus)\s*$", re.I)
PACK_WORD = re.compile(
    rf"\b(?:набор\w*|комплект\w*|set|kit|pack)\b|\b{COUNT}\s*{PIECES}\b|"
    rf"\b(?:по|each)\s+{NUM}", re.I)
NON_INTEGER_COUNT = re.compile(
    rf"(?:\d+[.,]\d+\s*{MULTIPLY}\s*{NUM}\s*(?:{UNIT_PATTERN})(?!\w)|"
    rf"{NUM}\s*(?:{UNIT_PATTERN})(?!\w)\s*{MULTIPLY}\s*\d+[.,]\d+)", re.I)
FOREIGN = re.compile(r"\b(?:fl\.?\s*oz|oz|унци\w*)\b", re.I)
SIGNED_AMOUNT = re.compile(
    rf"(?P<sign>[-−+])(?P<gap>\s*)(?P<value>{NUM})\s*(?:{UNIT_PATTERN})(?!\w)", re.I)
BAD_NUMBER = re.compile(rf"\d+(?:[.,]\d+){{2,}}\s*(?:{UNIT_PATTERN})(?!\w)", re.I)
RANGE_AMOUNT = re.compile(
    rf"(?<![\w.,-])(?P<low>[1-9]\d*(?:[.,]\d+)?)\s+[-−]\s*"
    rf"(?P<high>{NUM})\s*(?:{UNIT_PATTERN})(?!\w)", re.I)
NUMBER_MARKER = re.compile(r"(?:№|\bno\.?|\bn[°º])\s*$", re.I)
VOLUME_WITHOUT_UNIT = re.compile(
    rf"\b(?:объ[её]м(?:\s+(?:флакона|продукта|товара))?\s*[:=\-]?\s*|"
    rf"volume\s*[:=]\s*)(?P<value>{NUM})(?![\d.,])"
    rf"(?!\s*(?:{UNIT_PATTERN})(?!\w))(?!\s*(?:[%xх×*]|см\b|cm\b))", re.I)
DECLARED_MULTIPLICATION = re.compile(
    rf"^(?P<count>{COUNT})\s*{MULTIPLY}\s*(?P<value>{NUM})$", re.I)
DECLARED_PER_ITEM = re.compile(
    rf"^(?P<count>{COUNT})\s*{PIECES}\s*(?:по|each)\s*(?P<value>{NUM})$", re.I)
PERFUME_CUE = re.compile(
    r"\b(?:духи|парфюм\w*|одеколон\w*|perfume|parfum|edp|edt)\b|"
    r"\bтуалетн\w*\s+вод\w*\b|\beau\s+de\s+(?:parfum|toilette)\b", re.I)
LIST_SUM_CUE = re.compile(r"\b(?:refill|рефил\w*|запасн\w*\s+блок\w*)\b", re.I)
EXPLICIT_TOTAL = re.compile(
    rf"\b(?:общ(?:ий|его)\s+объ[её]м|суммарн\w*\s+объ[её]м|total\s+volume)\b"
    rf"\s*[:=\-]?\s*(?P<value>{NUM})\s*(?P<unit>{UNIT_PATTERN})(?!\w)", re.I)
TRAILING_NUMBER = re.compile(rf"(?<![\w.,+−-])(?P<value>{NUM})\s*$", re.I)
INCOMPLETE_UNIT = re.compile(
    rf"(?<![\d.,])(?P<value>{NUM})\s*(?P<unit>[мm])\.?\s*$", re.I)


@dataclass(frozen=True)
class QuantityProfile:
    """Category hints used only for otherwise ambiguous product names."""

    context_cue: re.Pattern
    list_sum_cue: re.Pattern = LIST_SUM_CUE

    @classmethod
    def from_words(cls, *words: str) -> "QuantityProfile":
        """Create a profile from complete category words."""
        if not words:
            return cls(re.compile(r"(?!x)x"), LIST_SUM_CUE)
        alternatives = "|".join(re.escape(word) for word in words)
        return cls(re.compile(rf"\b(?:{alternatives})\b", re.I), LIST_SUM_CUE)


GENERIC_PROFILE = QuantityProfile.from_words()
PERFUMERY_PROFILE = QuantityProfile(PERFUME_CUE, LIST_SUM_CUE)
