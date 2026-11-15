from __future__ import annotations

import re
import unicodedata
from typing import TypedDict

from carat_algorithms.core import CheckStatus
from carat_algorithms.text.volume.parsing import extract_amounts

PERFUME_TYPES = (
    "духи",
    "душистая вода",
    "лавандовая вода",
    "одеколон",
    "парфюмерная вода",
    "парфюмированная вода",
    "спрей для тела",
    "туалетная вода",
    "комплект",
    "парфюм",
    "парфюмерный спрей",
    "мист",
    "твердые духи",
)


class NameCompositionFinding(TypedDict):
    status: CheckStatus
    rule: str
    message: str
    field_refs: tuple[str, ...]


def normalize_text(value: str | None) -> str:
    """Normalize text for comparison."""
    if value is None:
        return ""

    text = unicodedata.normalize("NFKC", value).casefold().replace("ё", "е")
    text = re.sub(r"_+", " ", text)
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


_NORMALIZED_PERFUME_TYPES = frozenset(normalize_text(value) for value in PERFUME_TYPES)


def _remove_volumes(value: str) -> tuple[str, int]:
    """Remove volume expressions and return remaining text and their count.

    Mass expressions (g/kg) are deliberately preserved.
    Volume parsing is shared with the existing R5 implementation.
    """
    text = unicodedata.normalize("NFKC", value).replace("\u00a0", " ")

    volumes = [amount for amount in extract_amounts(text) if amount["dimension"] == "volume"]

    remaining = text

    for amount in volumes:
        remaining = remaining.replace(amount["fragment"], " ", 1)

    remaining = re.sub(r"\s+", " ", remaining).strip()

    return remaining, len(volumes)


def _finding(
    status: CheckStatus,
    rule: str,
    message: str,
    field_refs: tuple[str, ...],
) -> NameCompositionFinding:
    return {
        "status": status,
        "rule": rule,
        "message": message,
        "field_refs": field_refs,
    }


def check_name_composition(
    name: str,
    perfume_type: str | None,
) -> NameCompositionFinding:
    """Check product-name composition according to R6."""

    name_without_volume, volume_count = _remove_volumes(name)

    cleaned_name = normalize_text(name_without_volume)
    cleaned_type = normalize_text(perfume_type)

    if not cleaned_name:
        return _finding(
            CheckStatus.REVIEW,
            "NAME_COMPOSITION_VOLUME_ONLY",
            "Наименование содержит только обозначение объёма и не содержит описания товара.",
            ("fullName",),
        )

    if cleaned_type and cleaned_name == cleaned_type:
        return _finding(
            CheckStatus.WARNING,
            "NAME_COMPOSITION_ONLY_TYPE",
            f'После исключения объёма наименование "{name}" '
            f'состоит только из значения типа парфюмерии "{perfume_type}".',
            ("fullName", "perfumeryType"),
        )

    if cleaned_name in _NORMALIZED_PERFUME_TYPES:
        return _finding(
            CheckStatus.WARNING,
            "NAME_COMPOSITION_ONLY_TYPE",
            f'После исключения объёма наименование "{name}" состоит только из известного типа парфюмерии.',
            ("fullName",),
        )

    name_part_count = len(cleaned_name.split()) + volume_count

    if name_part_count == 1:
        return _finding(
            CheckStatus.WARNING,
            "NAME_COMPOSITION_SINGLE_WORD",
            f'Наименование "{name}" состоит из одного слова.',
            ("fullName",),
        )

    if perfume_type is None:
        return _finding(
            CheckStatus.NOT_CHECKED,
            "NAME_COMPOSITION_TYPE_MISSING",
            "Не указан атрибут «Тип парфюмерии», необходимый для проверки наименования.",
            ("fullName", "perfumeryType"),
        )

    if not perfume_type.strip():
        return _finding(
            CheckStatus.REVIEW,
            "NAME_COMPOSITION_TYPE_EMPTY",
            "Атрибут «Тип парфюмерии» пустой.",
            ("fullName", "perfumeryType"),
        )

    return _finding(
        CheckStatus.PASS,
        "NAME_COMPOSITION_OK",
        "Наименование содержит дополнительные сведения помимо типа парфюмерии.",
        ("fullName", "perfumeryType"),
    )
