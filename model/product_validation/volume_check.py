"""Проверка количества из наименования товара по правилам.

Как работает модуль
-------------------
1. Находит в названии явные количества с единицей: ``50 мл``, ``0,5 л``,
   ``200 г``. Числа без единицы не угадываются по значению атрибута.
2. Нормализует совместимые единицы (литры в миллилитры, килограммы в граммы).
3. Рассчитывает однозначные наборы: ``4 × 5 мл``, ``4 шт. по 5 мл`` и суммы.
4. Сравнивает найденное или рассчитанное количество с заявленным атрибутом.
5. Возвращает словарь с ``status``, ``rule``, объяснением и деталями расчёта.

Основная универсальная функция — :func:`check_quantity`. Она подходит для
товаров любых категорий, если количество записано с поддерживаемой единицей.
Неоднозначные записи без единицы зависят от профиля категории. Встроенный
``GENERIC_PROFILE`` не делает таких предположений, а ``PERFUMERY_PROFILE``
сохраняет все эвристики текущего проекта.

Для обратной совместимости :func:`check_volume` всегда использует
``PERFUMERY_PROFILE``. Поэтому ``check_catalog.py`` и существующие отчёты
продолжают работать без изменений. Названия полей результата и правил
``VOLUME_*`` также сохранены намеренно.

Пример для другой категории::

    cosmetics = QuantityProfile.from_words("шампунь", "крем", "гель")
    result = check_quantity("Шампунь 3 × 250 мл", 750, "мл", cosmetics)

Чтобы добавить новую единицу, внесите её в ``UNITS``. Масса и объём являются
разными размерностями и без известной плотности друг с другом не сравниваются.
"""
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

# ---------------------------------------------------------------------------
# Контракт входных полей текущей Excel-выгрузки
# ---------------------------------------------------------------------------

NAME = "Полное наименование товара (2478)"
VALUE = "Заявленный объем (2716)"
UNIT = "Тип (2716)"

# ---------------------------------------------------------------------------
# Единицы и базовые шаблоны
# ---------------------------------------------------------------------------

# Формат: написание -> (размерность, множитель, нормализованная единица).
# Массу сравниваем только с массой; плотность продукта не предполагаем.
UNITS = {
    "мл": ("volume", Decimal(1), "мл"), "ml": ("volume", Decimal(1), "мл"),
    "л": ("volume", Decimal(1000), "мл"), "l": ("volume", Decimal(1000), "мл"),
    "литр": ("volume", Decimal(1000), "мл"), "литра": ("volume", Decimal(1000), "мл"),
    "литров": ("volume", Decimal(1000), "мл"),
    "миллилитр": ("volume", Decimal(1), "мл"),
    "миллилитра": ("volume", Decimal(1), "мл"),
    "миллилитров": ("volume", Decimal(1), "мл"),
    "г": ("mass", Decimal(1), "г"), "g": ("mass", Decimal(1), "г"),
    "гр": ("mass", Decimal(1), "г"), "грамм": ("mass", Decimal(1), "г"),
    "грамма": ("mass", Decimal(1), "г"), "граммов": ("mass", Decimal(1), "г"),
    "кг": ("mass", Decimal(1000), "г"), "kg": ("mass", Decimal(1000), "г"),
}
UNIT_PATTERN = "|".join(re.escape(u) for u in sorted(UNITS, key=len, reverse=True))
NUM = r"\d+(?:[.,]\d+)?"
COUNT = r"\d+"
COUNT_START = rf"(?<![\d.,]){COUNT}"
PIECES = r"(?:шт\.?|штук(?:а|и)?|pcs?|pieces?)"
MULTIPLY = r"[xх×*]"
AMOUNT_TEXT = rf"(?P<value>{NUM})\s*(?P<unit>{UNIT_PATTERN})(?!\w)"

# Допускаем Blue100ml и Parfum,100 мл. Не извлекаем хвост дроби/числа.
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
    rf"volume\s*[:=]\s*)"
    rf"(?P<value>{NUM})(?![\d.,])"
    rf"(?!\s*(?:{UNIT_PATTERN})(?!\w))(?!\s*(?:[%xх×*]|см\b|cm\b))", re.I)
DECLARED_MULTIPLICATION = re.compile(
    rf"^(?P<count>{COUNT})\s*{MULTIPLY}\s*(?P<value>{NUM})$", re.I)
DECLARED_PER_ITEM = re.compile(
    rf"^(?P<count>{COUNT})\s*{PIECES}\s*(?:по|each)\s*(?P<value>{NUM})$", re.I)
PERFUME_CUE = re.compile(
    r"\b(?:духи|парфюм\w*|одеколон\w*|perfume|parfum|edp|edt)\b|"
    r"\bтуалетн\w*\s+вод\w*\b|"
    r"\beau\s+de\s+(?:parfum|toilette)\b", re.I)
LIST_SUM_CUE = re.compile(r"\b(?:refill|рефил\w*|запасн\w*\s+блок\w*)\b", re.I)
EXPLICIT_TOTAL = re.compile(
    rf"\b(?:общ(?:ий|его)\s+объ[её]м|суммарн\w*\s+объ[её]м|total\s+volume)\b"
    rf"\s*[:=\-]?\s*(?P<value>{NUM})\s*(?P<unit>{UNIT_PATTERN})(?!\w)", re.I)
TRAILING_NUMBER = re.compile(rf"(?<![\w.,+−-])(?P<value>{NUM})\s*$", re.I)
INCOMPLETE_UNIT = re.compile(
    rf"(?<![\d.,])(?P<value>{NUM})\s*(?P<unit>[мm])\.?\s*$", re.I)


@dataclass(frozen=True)
class QuantityProfile:
    """Категорийные подсказки для неоднозначных названий.

    Явные количества с полноценными единицами распознаются независимо от
    профиля. ``context_cue`` разрешает осторожно выделять конечное число без
    единицы или оборванную единицу, а ``list_sum_cue`` — состав из основного
    товара и дополнительного блока.
    """

    context_cue: re.Pattern
    list_sum_cue: re.Pattern = LIST_SUM_CUE

    @classmethod
    def from_words(cls, *words: str) -> "QuantityProfile":
        """Создать профиль из полных слов категории без регулярных выражений."""
        if not words:
            return cls(re.compile(r"(?!x)x"), LIST_SUM_CUE)
        alternatives = "|".join(re.escape(word) for word in words)
        return cls(re.compile(rf"\b(?:{alternatives})\b", re.I), LIST_SUM_CUE)


# Универсальный профиль анализирует только доказанные записи с единицами.
GENERIC_PROFILE = QuantityProfile.from_words()

# Этот профиль сохраняет поведение проекта для категории парфюмерии.
PERFUMERY_PROFILE = QuantityProfile(PERFUME_CUE, LIST_SUM_CUE)

__all__ = [
    "QuantityProfile",
    "GENERIC_PROFILE",
    "PERFUMERY_PROFILE",
    "check_quantity",
    "check_volume",
    "check_product_card",
]


# ---------------------------------------------------------------------------
# Нормализация входных значений
# ---------------------------------------------------------------------------


def text(value: Any) -> str:
    """Безопасно привести значение ячейки к очищенной строке."""
    if value is None:
        return ""
    try:
        if value != value:
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).replace("\u00a0", " ").strip()


def number(value: Any) -> Decimal:
    """Прочитать строго положительное десятичное число без единицы."""
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
    """Читаем обычное значение либо явное составное значение атрибута."""
    raw = text(value)
    try:
        return number(raw)
    except ValueError as original_error:
        match = DECLARED_MULTIPLICATION.fullmatch(raw) or DECLARED_PER_ITEM.fullmatch(raw)
        if not match:
            raise original_error
        count = Decimal(match['count'])
        item_value = Decimal(match['value'].replace(',', '.'))
        if count <= 0 or item_value <= 0:
            raise original_error
        return count * item_value


def formatted(value: Decimal) -> str:
    """Записать Decimal без экспоненты и лишних конечных нулей."""
    return format(value.normalize(), "f")


def _unit_data(value: str, unit: str) -> tuple[Decimal, str, Decimal, str]:
    """Вернуть исходное и нормализованное количество с размерностью."""
    amount = Decimal(value.replace(",", "."))
    dimension, factor, normalized_unit = UNITS[unit.lower()]
    return amount, dimension, amount * factor, normalized_unit


def _is_l_name(title: str, match: re.Match, unit_group: str) -> bool:
    """Отличить латинскую L в названии вроде L'Eau от обозначения литра."""
    return match[unit_group].lower() == "l" and bool(
        re.match(r"(?:['’`ʼ]|\.)\s*[a-zа-яё0-9]", title[match.end():], re.I))


def _is_catalog_code(match: re.Match, value_group: str, unit_group: str) -> bool:
    """Отличить код вроде ``064 G`` или ``00l`` от количества."""
    raw_value = match[value_group]
    unit = match[unit_group].lower()
    return (unit in ('l', 'g') and raw_value.isdigit() and len(raw_value) > 1
            and raw_value.startswith('0'))


# ---------------------------------------------------------------------------
# Извлечение и проверка неоднозначных записей
# ---------------------------------------------------------------------------

def has_concatenated_amount(name: Any) -> bool:
    """Находим склейки кода/названия и объёма, границу которых нельзя доказать."""
    title = text(name)
    for match in AMOUNT.finditer(title):
        raw_value = match['value']
        parts = re.split(r'[.,]', raw_value, maxsplit=1)
        if (len(parts) == 2 and len(parts[0]) >= 2 and parts[0].startswith('0')
                and parts[1].startswith('0')):
            return True
        if (len(parts) == 1 and match['unit'].lower() in ('мл', 'ml')
                and Decimal(raw_value) > 1000):
            return True
    return False


def ambiguous_number(title: str) -> bool:
    """Проверить признаки номера, диапазона или знакового количества."""
    if BAD_NUMBER.search(title):
        return True
    for range_match in RANGE_AMOUNT.finditer(title):
        low = Decimal(range_match['low'].replace(',', '.'))
        high = Decimal(range_match['high'].replace(',', '.'))
        if low < high:
            return True
    for match in SIGNED_AMOUNT.finditer(title):
        prefix = title[:match.start()].rstrip()
        # Плюс между двумя явными объёмами — сумма, а не знак числа.
        if match['sign'] == '+' and AMOUNT.search(prefix):
            continue
        # В товарных названиях дефис обычно отделяет объём от названия/кода.
        # Не разрешаем только знак в начале и числовые диапазоны 30-50 / 30 - 50.
        has_name = bool(re.search(r'[a-zа-яё]', prefix, re.I))
        separator = match['sign'] in '-−+' and has_name
        if not separator:
            return True
    for match in AMOUNT.finditer(title):
        if _is_l_name(title, match, 'unit') or _is_catalog_code(match, 'value', 'unit'):
            continue
        prefix = title[max(0, match.start()-15):match.start()]
        if NUMBER_MARKER.search(prefix):
            return True
    return False


def extract_amounts(name: Any) -> list[dict]:
    """Находим явные количества с известной единицей; числа без единиц не угадываем."""
    title = text(name)
    result = []
    for match in AMOUNT.finditer(title):
        if (_is_l_name(title, match, 'unit')
                or _is_catalog_code(match, 'value', 'unit')):
            continue
        raw_value = match['value']
        # Выгрузка иногда склеивает номер варианта и объём: 83,1000мл.
        # Узкое правило не затрагивает обычные дроби 7,5 мл и 0,005 л.
        separator_parts = re.split(r'([.,])', raw_value, maxsplit=1)
        if len(separator_parts) == 3:
            integer, separator, fraction = separator_parts
            leading_zero_code = (len(integer) >= 2 and integer.startswith('0')
                                 and fraction and not fraction.startswith('0'))
            comma_catalog_number = (separator == ',' and len(integer) >= 2
                                    and len(fraction) >= 3)
            if leading_zero_code or comma_catalog_number:
                raw_value = fraction
        value, dimension, normalized, normalized_unit = _unit_data(raw_value, match['unit'])
        result.append({"fragment": match.group(), "value": formatted(value),
                       "unit": match['unit'].lower(), "dimension": dimension,
                       "normalized_value": formatted(normalized),
                       "normalized_unit": normalized_unit})
    return result


def extract_explicit_total(name: Any) -> dict | None:
    """Явно подписанный общий объём имеет приоритет над объёмами компонентов."""
    match = EXPLICIT_TOTAL.search(text(name))
    if not match:
        return None
    value, dimension, normalized, normalized_unit = _unit_data(
        match['value'], match['unit'])
    return {"fragment": match.group(), "value": formatted(value),
            "unit": match['unit'].lower(), "dimension": dimension,
            "normalized_value": formatted(normalized),
            "normalized_unit": normalized_unit}


def extract_volume_without_unit(
        name: Any, profile: QuantityProfile = PERFUMERY_PROFILE) -> str | None:
    """Ищем число без единицы только рядом с явным словом «объём/volume»."""
    title = text(name)
    match = VOLUME_WITHOUT_UNIT.search(title)
    if match:
        return match['value']
    if profile.context_cue.search(title):
        match = TRAILING_NUMBER.search(title)
        if match and not NUMBER_MARKER.search(title[:match.start()]):
            return match['value']
    return None


def extract_incomplete_unit(
        name: Any, profile: QuantityProfile = PERFUMERY_PROFILE
) -> tuple[str, str] | None:
    """Находим конечное «30 м/m»: это возможное, но не доказанное «30 мл/ml»."""
    title = text(name)
    if not profile.context_cue.search(title):
        return None
    match = INCOMPLETE_UNIT.search(title)
    return (match['value'], match['unit']) if match else None


def extract_set(
        name: Any, profile: QuantityProfile = PERFUMERY_PROFILE) -> dict | None:
    """Возвращает однозначный расчёт набора либо описание причины неоднозначности."""
    title = text(name)
    terms = []
    for match in SET_TERM.finditer(title):
        kind = next(k for k in ('per', 'prefix', 'suffix', 'single') if match[k] is not None)
        if (_is_l_name(title, match, f'{kind}_unit')
                or _is_catalog_code(match, f'{kind}_value', f'{kind}_unit')):
            continue
        raw_count = match[f'{kind}_count'] if kind != 'single' else '1'
        count = Decimal(raw_count)
        value, dimension, normalized, normalized_unit = _unit_data(
            match[f'{kind}_value'], match[f'{kind}_unit'])
        terms.append({"kind": kind, "start": match.start(), "end": match.end(),
                      "count": count, "value": value,
                      "unit": match[f'{kind}_unit'].lower(), "dimension": dimension,
                      "normalized_item": normalized, "normalized_unit": normalized_unit})

    multiplied = any(term['kind'] != 'single' for term in terms)
    gaps = [title[left['end']:right['start']] for left, right in zip(terms, terms[1:])]
    sum_chain = len(terms) > 1 and all(
        SUM_SEPARATOR.fullmatch(gap) for gap in gaps)
    listed_product_components = (
        len(terms) >= 3 and len(profile.context_cue.findall(title)) >= 3
        and all(',' in gap or ';' in gap for gap in gaps))
    refill_components = (
        len(terms) == 2 and bool(profile.list_sum_cue.search(title))
        and terms[0]['normalized_item'] != terms[1]['normalized_item'])
    listed_components = listed_product_components or refill_components
    signatures = {(term['kind'], term['count'], term['dimension'],
                   term['normalized_item']) for term in terms}
    if len(terms) > 1 and not sum_chain and not listed_components and len(signatures) == 1:
        # Одинаковый объём/набор нередко повторён на двух языках.
        terms = [terms[0]]
        multiplied = terms[0]['kind'] != 'single'
    if not multiplied and not sum_chain and not listed_components:
        return None
    if listed_components:
        sum_chain = True
    if len(terms) > 1 and not sum_chain:
        return {"ambiguous": True, "reason": "части набора не соединены явным знаком суммы"}
    if any(term['count'] <= 0 or term['value'] <= 0 for term in terms):
        return {"ambiguous": True, "reason": "количество единиц или объём должен быть больше нуля"}
    dimensions = {term['dimension'] for term in terms}
    if len(dimensions) != 1:
        return {"ambiguous": True, "reason": "в составе смешаны масса и объём"}

    total_count = sum((term['count'] for term in terms), Decimal(0))
    total = sum((term['count'] * term['normalized_item'] for term in terms), Decimal(0))
    item_sizes = {term['normalized_item'] for term in terms}
    normalized_unit = terms[0]['normalized_unit']
    components = [{"count": formatted(term['count']),
                   "item_value": formatted(term['value']), "item_unit": term['unit'],
                   "normalized_item_value": formatted(term['normalized_item']),
                   "normalized_unit": normalized_unit,
                   "subtotal": formatted(term['count'] * term['normalized_item'])}
                  for term in terms]
    return {"ambiguous": False, "dimension": terms[0]['dimension'],
            "item_count": formatted(total_count),
            "item_volume": (f"{formatted(next(iter(item_sizes)))} {normalized_unit}"
                            if len(item_sizes) == 1 else None),
            "calculated_total_value": formatted(total),
            "calculated_total": f"{formatted(total)} {normalized_unit}",
            "normalized_unit": normalized_unit, "components": components}


def _calculation_message(set_data: dict, declared: Decimal, declared_unit: str) -> str:
    """Собрать человекочитаемое объяснение расчёта набора."""
    parts = [f"{c['count']} × {c['normalized_item_value']} {c['normalized_unit']}"
             for c in set_data['components']]
    expression = " + ".join(parts)
    return (f"{expression} = {set_data['calculated_total']}; "
            f"заявлено {formatted(declared)} {declared_unit}.")


# ---------------------------------------------------------------------------
# Основная проверка
# ---------------------------------------------------------------------------

def check_quantity(
        name: Any,
        declared_value: Any,
        declared_unit: Any,
        profile: QuantityProfile = GENERIC_PROFILE,
) -> dict:
    """Сравнить количество в названии с отдельным атрибутом карточки.

    Аргументы:
        name: полное наименование товара;
        declared_value: значение отдельного атрибута без единицы либо
            поддерживаемое выражение вида ``3 × 11``;
        declared_unit: отдельная единица измерения атрибута;
        profile: категорийные подсказки. Для очевидных записей ``50 мл`` или
            ``4 × 5 мл`` профиль не требуется.

    Возвращаемый ``status`` описывает только этот критерий и не подтверждает
    корректность всей карточки. Имена полей и ``VOLUME_*`` правил сохранены
    ради совместимости с существующими CSV/XLSX/JSON отчётами.
    """
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
        # Не складываем «объём каждого 10 мл, общий объём 30 мл» как 40 мл.
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
        message = _calculation_message(set_data, normalized, normalized_unit)
        if Decimal(set_data['calculated_total_value']) == normalized:
            return finish("ok", "VOLUME_SET_MATCH", message)
        return finish("warning", "VOLUME_SET_MISMATCH", message)

    # Неполные признаки комплекта с единицей не превращаем в произвольный расчёт.
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
    if any(Decimal(a['value']) <= 0 for a in amounts):
        return finish("manual_review", "VOLUME_INVALID_NAME",
                      "В названии указано нулевое количество.")
    distinct = {(a['dimension'], a['normalized_value']) for a in amounts}
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


# ---------------------------------------------------------------------------
# Совместимые обёртки текущего проекта
# ---------------------------------------------------------------------------

def check_volume(name: Any, declared_volume: Any, declared_unit: Any) -> dict:
    """Проверить карточку с прежними парфюмерными эвристиками.

    Это стабильный публичный интерфейс текущего проекта. Для новых категорий
    вызывайте :func:`check_quantity` с ``GENERIC_PROFILE`` или собственным
    :class:`QuantityProfile`.
    """
    return check_quantity(
        name, declared_volume, declared_unit, profile=PERFUMERY_PROFILE)


def check_product_card(card: Mapping[str, Any]) -> dict:
    """Прочитать поля текущей карточки CARAT и вызвать ``check_volume``."""
    def field(*keys):
        return next((card[k] for k in keys if k in card), None)
    return check_volume(field(NAME, "fullName", "name"),
                        field(VALUE, "volume", "declared_volume"),
                        field(UNIT, "volume_unit", "declared_unit"))
