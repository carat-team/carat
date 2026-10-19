"""Normalization, extraction, ambiguity detection, and set calculation."""

import re
from decimal import Decimal, InvalidOperation
from typing import Any

from .config import (
    AMOUNT, BAD_NUMBER, DECLARED_MULTIPLICATION, DECLARED_PER_ITEM,
    EXPLICIT_TOTAL, INCOMPLETE_UNIT, NUMBER_MARKER, RANGE_AMOUNT, SET_TERM,
    SIGNED_AMOUNT, SUM_SEPARATOR, TRAILING_NUMBER, UNITS,
    VOLUME_WITHOUT_UNIT, PERFUMERY_PROFILE, QuantityProfile,
)


def text(value: Any) -> str:
    """Convert a spreadsheet/API value to a clean string."""
    if value is None:
        return ""
    try:
        if value != value:  # NaN
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).replace("\u00a0", " ").strip()


def number(value: Any) -> Decimal:
    """Parse a strictly positive decimal number without a unit."""
    raw = text(value).replace(",", ".")
    if not re.fullmatch(r"\d+(?:\.\d+)?", raw):
        raise ValueError("Ожидалось положительное число без единицы измерения.")
    try:
        result = Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError("Некорректное число.") from exc
    if not result.is_finite() or result <= 0:
        raise ValueError("Количество должно быть больше нуля.")
    return result


def declared_number(value: Any) -> Decimal:
    """Parse a scalar or a declared expression such as ``3 × 11``."""
    raw = text(value)
    try:
        return number(raw)
    except ValueError as original_error:
        match = DECLARED_MULTIPLICATION.fullmatch(raw) or DECLARED_PER_ITEM.fullmatch(raw)
        if not match:
            raise original_error
        count = Decimal(match["count"])
        item_value = Decimal(match["value"].replace(",", "."))
        if count <= 0 or item_value <= 0:
            raise original_error
        return count * item_value


def formatted(value: Decimal) -> str:
    """Format Decimal without exponent notation or redundant zeroes."""
    return format(value.normalize(), "f")


def unit_data(value: str, unit: str) -> tuple[Decimal, str, Decimal, str]:
    """Return raw value, dimension, normalized value, and canonical unit."""
    amount = Decimal(value.replace(",", "."))
    dimension, factor, normalized_unit = UNITS[unit.lower()]
    return amount, dimension, amount * factor, normalized_unit


def _is_l_name(title: str, match: re.Match, unit_group: str) -> bool:
    """Distinguish the letter L in L'Eau/L.12 from liters."""
    return match[unit_group].lower() == "l" and bool(
        re.match(r"(?:['’`ʼ]|\.)\s*[a-zа-яё0-9]", title[match.end():], re.I))


def _is_catalog_code(match: re.Match, value_group: str, unit_group: str) -> bool:
    """Distinguish catalog codes such as ``064 G`` and ``00l``."""
    raw_value = match[value_group]
    unit = match[unit_group].lower()
    return (unit in ("l", "g") and raw_value.isdigit() and len(raw_value) > 1
            and raw_value.startswith("0"))


def has_concatenated_amount(name: Any) -> bool:
    """Detect code/amount concatenations whose boundary cannot be proven."""
    title = text(name)
    for match in AMOUNT.finditer(title):
        raw_value = match["value"]
        parts = re.split(r"[.,]", raw_value, maxsplit=1)
        if (len(parts) == 2 and len(parts[0]) >= 2 and parts[0].startswith("0")
                and parts[1].startswith("0")):
            return True
        if (len(parts) == 1 and match["unit"].lower() in ("мл", "ml")
                and Decimal(raw_value) > 1000):
            return True
    return False


def ambiguous_number(title: str) -> bool:
    """Detect malformed decimals, ranges, signs, and aroma/model numbers."""
    if BAD_NUMBER.search(title):
        return True
    for range_match in RANGE_AMOUNT.finditer(title):
        low = Decimal(range_match["low"].replace(",", "."))
        high = Decimal(range_match["high"].replace(",", "."))
        if low < high:
            return True
    for match in SIGNED_AMOUNT.finditer(title):
        prefix = title[:match.start()].rstrip()
        if match["sign"] == "+" and AMOUNT.search(prefix):
            continue
        has_name = bool(re.search(r"[a-zа-яё]", prefix, re.I))
        if not (match["sign"] in "-−+" and has_name):
            return True
    for match in AMOUNT.finditer(title):
        if _is_l_name(title, match, "unit") or _is_catalog_code(match, "value", "unit"):
            continue
        prefix = title[max(0, match.start() - 15):match.start()]
        if NUMBER_MARKER.search(prefix):
            return True
    return False


def extract_amounts(name: Any) -> list[dict]:
    """Extract quantities with supported units; never infer a missing unit."""
    title = text(name)
    result = []
    for match in AMOUNT.finditer(title):
        if (_is_l_name(title, match, "unit")
                or _is_catalog_code(match, "value", "unit")):
            continue
        raw_value = match["value"]
        parts = re.split(r"([.,])", raw_value, maxsplit=1)
        if len(parts) == 3:
            integer, separator, fraction = parts
            leading_zero_code = (len(integer) >= 2 and integer.startswith("0")
                                 and fraction and not fraction.startswith("0"))
            comma_catalog_number = (separator == "," and len(integer) >= 2
                                    and len(fraction) >= 3)
            if leading_zero_code or comma_catalog_number:
                raw_value = fraction
        value, dimension, normalized, normalized_unit = unit_data(
            raw_value, match["unit"])
        result.append({"fragment": match.group(), "value": formatted(value),
                       "unit": match["unit"].lower(), "dimension": dimension,
                       "normalized_value": formatted(normalized),
                       "normalized_unit": normalized_unit})
    return result


def extract_explicit_total(name: Any) -> dict | None:
    """Extract a labeled total, which has priority over component amounts."""
    match = EXPLICIT_TOTAL.search(text(name))
    if not match:
        return None
    value, dimension, normalized, normalized_unit = unit_data(
        match["value"], match["unit"])
    return {"fragment": match.group(), "value": formatted(value),
            "unit": match["unit"].lower(), "dimension": dimension,
            "normalized_value": formatted(normalized),
            "normalized_unit": normalized_unit}


def extract_volume_without_unit(
        name: Any, profile: QuantityProfile = PERFUMERY_PROFILE) -> str | None:
    """Extract a unitless number only from explicit volume/category context."""
    title = text(name)
    match = VOLUME_WITHOUT_UNIT.search(title)
    if match:
        return match["value"]
    if profile.context_cue.search(title):
        match = TRAILING_NUMBER.search(title)
        if match and not NUMBER_MARKER.search(title[:match.start()]):
            return match["value"]
    return None


def extract_incomplete_unit(
        name: Any, profile: QuantityProfile = PERFUMERY_PROFILE
) -> tuple[str, str] | None:
    """Detect trailing ``30 м/m`` that may be incomplete ``мл/ml``."""
    title = text(name)
    if not profile.context_cue.search(title):
        return None
    match = INCOMPLETE_UNIT.search(title)
    return (match["value"], match["unit"]) if match else None


def extract_set(
        name: Any, profile: QuantityProfile = PERFUMERY_PROFILE) -> dict | None:
    """Return an unambiguous set calculation or an ambiguity reason."""
    title = text(name)
    terms = []
    for match in SET_TERM.finditer(title):
        kind = next(k for k in ("per", "prefix", "suffix", "single")
                    if match[k] is not None)
        if (_is_l_name(title, match, f"{kind}_unit")
                or _is_catalog_code(match, f"{kind}_value", f"{kind}_unit")):
            continue
        raw_count = match[f"{kind}_count"] if kind != "single" else "1"
        count = Decimal(raw_count)
        value, dimension, normalized, normalized_unit = unit_data(
            match[f"{kind}_value"], match[f"{kind}_unit"])
        terms.append({"kind": kind, "start": match.start(), "end": match.end(),
                      "count": count, "value": value,
                      "unit": match[f"{kind}_unit"].lower(),
                      "dimension": dimension, "normalized_item": normalized,
                      "normalized_unit": normalized_unit})

    multiplied = any(term["kind"] != "single" for term in terms)
    gaps = [title[left["end"]:right["start"]]
            for left, right in zip(terms, terms[1:])]
    sum_chain = len(terms) > 1 and all(
        SUM_SEPARATOR.fullmatch(gap) for gap in gaps)
    listed_product_components = (
        len(terms) >= 3 and len(profile.context_cue.findall(title)) >= 3
        and all("," in gap or ";" in gap for gap in gaps))
    refill_components = (
        len(terms) == 2 and bool(profile.list_sum_cue.search(title))
        and terms[0]["normalized_item"] != terms[1]["normalized_item"])
    listed_components = listed_product_components or refill_components
    signatures = {(term["kind"], term["count"], term["dimension"],
                   term["normalized_item"]) for term in terms}
    if (len(terms) > 1 and not sum_chain and not listed_components
            and len(signatures) == 1):
        terms = [terms[0]]  # Same representation repeated in two languages.
        multiplied = terms[0]["kind"] != "single"
    if not multiplied and not sum_chain and not listed_components:
        return None
    if listed_components:
        sum_chain = True
    if len(terms) > 1 and not sum_chain:
        return {"ambiguous": True,
                "reason": "части набора не соединены явным знаком суммы"}
    if any(term["count"] <= 0 or term["value"] <= 0 for term in terms):
        return {"ambiguous": True,
                "reason": "количество единиц или объём должен быть больше нуля"}
    dimensions = {term["dimension"] for term in terms}
    if len(dimensions) != 1:
        return {"ambiguous": True, "reason": "в составе смешаны масса и объём"}

    total_count = sum((term["count"] for term in terms), Decimal(0))
    total = sum((term["count"] * term["normalized_item"] for term in terms),
                Decimal(0))
    item_sizes = {term["normalized_item"] for term in terms}
    normalized_unit = terms[0]["normalized_unit"]
    components = [{"count": formatted(term["count"]),
                   "item_value": formatted(term["value"]),
                   "item_unit": term["unit"],
                   "normalized_item_value": formatted(term["normalized_item"]),
                   "normalized_unit": normalized_unit,
                   "subtotal": formatted(term["count"] * term["normalized_item"])}
                  for term in terms]
    return {"ambiguous": False, "dimension": terms[0]["dimension"],
            "item_count": formatted(total_count),
            "item_volume": (f"{formatted(next(iter(item_sizes)))} {normalized_unit}"
                            if len(item_sizes) == 1 else None),
            "calculated_total_value": formatted(total),
            "calculated_total": f"{formatted(total)} {normalized_unit}",
            "normalized_unit": normalized_unit, "components": components}


def calculation_message(set_data: dict, declared: Decimal, unit: str) -> str:
    """Build a human-readable explanation of a set calculation."""
    parts = [f"{part['count']} × {part['normalized_item_value']} "
             f"{part['normalized_unit']}" for part in set_data["components"]]
    return (f"{' + '.join(parts)} = {set_data['calculated_total']}; "
            f"заявлено {formatted(declared)} {unit}.")
