"""Public orchestration of the product quantity validation rules."""

from decimal import Decimal
from typing import Any, Mapping

from .config import (
    FOREIGN, GENERIC_PROFILE, NAME, NON_INTEGER_COUNT, PACK_WORD,
    PERFUMERY_PROFILE, QuantityProfile, UNIT, UNITS, VALUE,
)
from .parsing import (
    ambiguous_number, calculation_message, declared_number, extract_amounts,
    extract_explicit_total, extract_incomplete_unit, extract_set,
    extract_volume_without_unit, formatted, has_concatenated_amount, text,
)


def check_quantity(
        name: Any,
        declared_value: Any,
        declared_unit: Any,
        profile: QuantityProfile = GENERIC_PROFILE,
) -> dict:
    """Compare quantity in a product name with its structured attribute."""
    result = {"status": None, "rule": None, "message": "", "detected_amounts": [],
              "declared_value": text(declared_value), "declared_unit": text(declared_unit),
              "normalized_declared_value": None, "normalized_unit": None,
              "item_count": None, "item_volume": None, "calculated_total": None,
              "set_components": []}

    def finish(status, rule, message):
        result.update(status=status, rule=rule, message=message)
        return result

    title = text(name)
    if not title or not text(declared_value) or not text(declared_unit):
        return finish("not_checked", "VOLUME_MISSING_INPUT",
                      "Нет наименования, заявленного количества или единицы.")
    try:
        value = declared_number(declared_value)
    except ValueError:
        return finish("manual_review", "VOLUME_INVALID_DECLARED",
                      "Заявленное количество не является положительным числом или поддерживаемым составным выражением.")
    unit_key = text(declared_unit).lower().rstrip('.')
    if unit_key not in UNITS:
        return finish("manual_review", "VOLUME_UNKNOWN_UNIT",
                      "Единица атрибута не поддерживается.")
    dimension, factor, normalized_unit = UNITS[unit_key]
    normalized = value * factor
    result.update(normalized_declared_value=formatted(normalized), normalized_unit=normalized_unit)
    amounts = extract_amounts(title)
    explicit_total = extract_explicit_total(title)
    if explicit_total is not None:
        # Do not add "each bottle 10 ml, total volume 30 ml" as 40 ml.
        amounts = [explicit_total]
    result['detected_amounts'] = amounts
    if FOREIGN.search(title):
        return finish("manual_review", "VOLUME_FOREIGN_UNIT",
                      "В названии есть унции; перевод не настроен.")
    if ambiguous_number(title):
        return finish("manual_review", "VOLUME_NUMBER_AMBIGUOUS",
                      "Неоднозначная запись количества, знак или номер аромата рядом с единицей.")
    if has_concatenated_amount(title):
        return finish(
            "manual_review", "VOLUME_CONCATENATED_NUMBER",
            "Число похоже на склейку номера модели и объёма; границу нельзя определить надёжно.")

    set_data = None if explicit_total is not None else extract_set(title, profile)
    if set_data is not None:
        if set_data['ambiguous']:
            return finish("manual_review", "VOLUME_SET_AMBIGUOUS",
                          f"Неоднозначный состав набора: {set_data['reason']}.")
        result.update(item_count=set_data['item_count'], item_volume=set_data['item_volume'],
                      calculated_total=set_data['calculated_total'],
                      set_components=set_data['components'])
        if set_data['dimension'] != dimension:
            return finish("manual_review", "VOLUME_SET_AMBIGUOUS",
                          "Расчётный состав и заявленное количество имеют разные размерности.")
        message = calculation_message(set_data, normalized, normalized_unit)
        if Decimal(set_data['calculated_total_value']) == normalized:
            return finish("ok", "VOLUME_SET_MATCH", message)
        return finish("warning", "VOLUME_SET_MISMATCH", message)

    # Do not turn incomplete pack hints into an arbitrary calculation.
    if NON_INTEGER_COUNT.search(title):
        return finish("manual_review", "VOLUME_SET_AMBIGUOUS",
                      "Количество единиц набора не является целым числом.")
    if explicit_total is None and PACK_WORD.search(title):
        return finish("manual_review", "VOLUME_SET_AMBIGUOUS",
                      "Есть признаки набора, но его состав нельзя однозначно рассчитать.")
    if not amounts:
        incomplete = extract_incomplete_unit(title, profile)
        if incomplete is not None:
            incomplete_value, incomplete_unit = incomplete
            return finish(
                "manual_review", "VOLUME_UNIT_INCOMPLETE",
                f"В названии найдено «{incomplete_value} {incomplete_unit}»: обозначение "
                f"единицы может быть неполным. Заявлено {formatted(normalized)} {normalized_unit}.")
        unitless_value = extract_volume_without_unit(title, profile)
        if unitless_value is not None:
            return finish(
                "manual_review", "VOLUME_UNIT_MISSING",
                f"В названии найдено число {unitless_value} без единицы; это может быть "
                f"объём или часть названия. Заявлено {formatted(normalized)} {normalized_unit}.")
        return finish("not_checked", "VOLUME_NOT_FOUND",
                      "В названии не найдено количество с поддерживаемой единицей.")
    if any(Decimal(amount['value']) <= 0 for amount in amounts):
        return finish("manual_review", "VOLUME_INVALID_NAME",
                      "В названии указано нулевое количество.")
    distinct = {(amount['dimension'], amount['normalized_value']) for amount in amounts}
    if len(distinct) > 1:
        return finish("manual_review", "VOLUME_MULTIPLE",
                      "В названии несколько разных количеств; нельзя однозначно выбрать одно.")
    detected_dimension, detected_value = next(iter(distinct))
    if detected_dimension != dimension:
        return finish("manual_review", "VOLUME_DIMENSION",
                      "Массу и объём нельзя сравнить без плотности.")
    if Decimal(detected_value) == normalized:
        return finish("ok", "VOLUME_MATCH",
                      f"Количество в названии и атрибуте совпадает: {detected_value} {normalized_unit}.")
    return finish("warning", "VOLUME_MISMATCH",
                  f"В названии: {detected_value} {normalized_unit}; "
                  f"в атрибуте: {formatted(normalized)} {normalized_unit}.")


def check_volume(name: Any, declared_volume: Any, declared_unit: Any) -> dict:
    """Run the current criterion with its perfumery-specific profile."""
    return check_quantity(
        name, declared_volume, declared_unit, profile=PERFUMERY_PROFILE)


def check_product_card(card: Mapping[str, Any]) -> dict:
    """Read supported CARAT field aliases and validate one product card."""
    def field(*keys):
        return next((card[key] for key in keys if key in card), None)

    return check_volume(field(NAME, "fullName", "name"),
                        field(VALUE, "volume", "declared_volume"),
                        field(UNIT, "volume_unit", "declared_unit"))
