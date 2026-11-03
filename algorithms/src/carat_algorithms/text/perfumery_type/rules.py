"""
Алгоритмическая проверка: 'Наименование товара не соответствует типу парфюмерии'.

Проверка сопоставляет явные обозначения типа парфюмерии в наименовании товара
со структурированным атрибутом 'Тип парфюмерии'.

Результат содержит:
    status: CheckStatus.PASS | CheckStatus.WARNING | CheckStatus.REVIEW | CheckStatus.NOT_CHECKED
    rule: постоянный идентификатор правила
    message: пояснение для проверяющего
    detected_type: нормализованный тип, определённый по наименованию, или None
    declared_type: нормализованный тип из атрибута или None
"""

from __future__ import annotations

import math
import re
from typing import TypedDict

from carat_algorithms.core import CheckStatus

# Справочник типов парфюмерии: канонический тип -> регулярные выражения для названия.
# Канонические значения должны соответствовать значениям в исходном каталоге.
# Порядок записей не важен: пересекающиеся совпадения разрешаются в
# detect_types_in_name() по длине совпадения (побеждает более длинное).
_TYPE_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "парфюмированная вода",
        (
            r"\bпарфюмированн(?:ая|ой|ую|ые|ых|ыми)\s+вод(?:а|ы|у|е|ой)\b",
            r"\bпарфюмерн(?:ая|ой|ую|ые|ых|ыми)\s+вод(?:а|ы|у|е|ой)\b",
            r"\beau\s+de\s+parfum\b",
            r"\bedp\b",
            r"\bпарфвода\b",
        ),
    ),
    (
        "туалетная вода",
        (
            r"\bтуалетн(?:ая|ой|ую|ые|ых|ыми)\s+вод(?:а|ы|у|е|ой)\b",
            r"\beau\s+de\s+toilette\b",
            r"\bparfum\s+de\s+toilette\b",
            r"\bedt\b",
        ),
    ),
    (
        "одеколон",
        (
            r"\bодеколон(?:а|е|ом|ы)?\b",
            r"\beau\s+de\s+cologne\b",
            r"\bedc\b",
        ),
    ),
    (
        "духи",
        (
            r"\bдух(?:и|ов|ам|ами|ах)\b",
            r"\bпарфюм\b",
            r"\bparfum\b",
            r"\bperfume(?!\s+mist\b)\b",
            r"\bextrait\s+de\s+parfum\b",
            r"\bпарфюмерн(?:ый|ого|ым)\s+экстракт(?:а|ом)?\b",
        ),
    ),
    (
        "парфюмерный спрей",
        (
            r"\bпарфюмерн\w*\s+спре[йяею]\w*\b",
            r"\bperfume\s+mist\b",
        ),
    ),
    (
        "мист",
        (
            r"\b(?:body|hair|fragrance)\s+mist\b",
            r"\bмист\b",
        ),
    ),
    (
        "твердые духи",
        (
            r"\bтв[её]рд\w*\s+дух\w*\b",
            r"\bsolid\s+perfume\b",
        ),
    ),
)

# Синонимы и варианты значений для типа парфюмерии.
_TYPE_ALIASES = {
    "духи": "духи",
    "парфюм": "духи",
    "parfum": "духи",
    "perfume": "духи",
    "парфюмированная вода": "парфюмированная вода",
    "парфюмерная вода": "парфюмированная вода",
    "eau de parfum": "парфюмированная вода",
    "edp": "парфюмированная вода",
    "туалетная вода": "туалетная вода",
    "eau de toilette": "туалетная вода",
    "edt": "туалетная вода",
    "одеколон": "одеколон",
    "eau de cologne": "одеколон",
    "edc": "одеколон",
    "парфюмерный спрей": "парфюмерный спрей",
    "спрей для тела": "мист",
    "мист": "мист",
    "твердые духи": "твердые духи",
    "твёрдые духи": "твердые духи",
}


def _is_missing(value: object) -> bool:
    """None и float NaN считаются пустыми (без зависимости от pandas)."""
    return value is None or (isinstance(value, float) and math.isnan(value))


# Приводит входное значение к единому виду: убирает лишние пробелы и знаки,
# заменяет 'ё' на 'е' и безопасно обрабатывает пустые значения и NaN.
def _normalize_text(value: object) -> str:
    if _is_missing(value):
        return ""
    text = str(value).lower().replace("ё", "е")
    text = re.sub(r"[\u00a0]+", " ", text)
    text = re.sub(r"[_/|]+", " ", text)
    text = re.sub(r"[^\w\s-]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


# Пары (тип в названии, тип в атрибуте), которые считаются совместимыми, хотя типы
# не равны. Твёрдые духи - разновидность духов, отдельного значения для них в
# справочнике 'Тип парфюмерии' нет. Чтобы отключить правило, оставьте множество пустым.
_COMPATIBLE_TYPES = frozenset({("твердые духи", "духи")})

# Типы атрибута, которые допустимы, если слово встречается в названии не первым.
# 'Духи' часто стоит в конце названия как формат ('… Eau de Parfum духи 15мл'), поэтому
# при атрибуте ДУХИ такие карточки считаются совпадением. Чтобы отключить правило,
# оставьте множество пустым.
_ACCEPTED_ANYWHERE = frozenset({"духи"})

# Значения атрибута 'комплект' / 'набор' (в том числе внутри составных значений,
# например 'Набор; Духи'). Для таких карточек проверка названия не выполняется:
# в наборе может быть несколько разных типов парфюмерии, поэтому вывод
# 'совпадает' или 'не совпадает' был бы необоснованным.
_BUNDLE_RE = re.compile(r"(?<!\w)(?:комплект|набор)(?!\w)")

_SORTED_ALIASES = sorted(_TYPE_ALIASES.items(), key=lambda item: len(item[0]), reverse=True)


# Находит в значении атрибута все известные типы. Более длинные синонимы проверяются
# первыми и 'съедают' своё место, поэтому 'твёрдые духи' не считаются ещё и 'духами'.
def _find_declared_types(value: object) -> set[str]:
    text = _normalize_text(value)
    if not text:
        return set()
    if text in _TYPE_ALIASES:
        return {_TYPE_ALIASES[text]}
    found: set[str] = set()
    for alias, canonical in _SORTED_ALIASES:
        pattern = r"(?<!\w)" + re.escape(alias) + r"(?!\w)"
        if re.search(pattern, text):
            found.add(canonical)
            text = re.sub(pattern, " ", text)
    return found


# Преобразует значение атрибута к каноническому типу. Если значение пустое, не
# распознано или содержит несколько разных типов ('EDT; ДУХИ') - возвращает None.
def normalize_declared_type(value: object) -> str | None:
    found = _find_declared_types(value)
    return next(iter(found)) if len(found) == 1 else None


# Ищет в названии все обозначения типов. Если одно обозначение лежит внутри более
# длинного ('parfum' в 'eau de parfum'), учитывается только длинное.
# Возвращает канонические типы без повторов в порядке появления в названии.
def detect_types_in_name(name: object) -> list[str]:
    text = _normalize_text(name)
    if not text:
        return []

    matches: list[tuple[int, int, str]] = []
    for canonical, patterns in _TYPE_PATTERNS:
        for pattern in patterns:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                matches.append((match.start(), match.end(), canonical))

    kept: list[tuple[int, int, str]] = []
    for item in sorted(matches, key=lambda m: (-(m[1] - m[0]), m[0])):
        if all(item[1] <= k[0] or item[0] >= k[1] for k in kept):
            kept.append(item)

    ordered: list[str] = []
    for _, _, canonical in sorted(kept):
        if canonical not in ordered:
            ordered.append(canonical)
    return ordered


# Тип по названию: None - маркера нет, \"ambiguous\" - в названии несколько разных
# типов, иначе - канонический тип.
def detect_type_in_name(name: object) -> str | None:
    types = detect_types_in_name(name)
    if not types:
        return None
    return types[0] if len(types) == 1 else "ambiguous"


class PerfumeryFinding(TypedDict):
    status: CheckStatus
    rule: str
    message: str
    detected_type: str | None
    declared_type: str | None


def _result(
    status: CheckStatus, rule: str, message: str, detected: str | None, declared: str | None
) -> PerfumeryFinding:
    return {
        "status": status,
        "rule": rule,
        "message": message,
        "detected_type": detected,
        "declared_type": declared,
    }


# Сравнивает распознанный в названии тип с типом атрибута и возвращает статус,
# идентификатор правила и пояснение для проверки карточки.
def check_perfumery_name(name: object, declared_type: object) -> PerfumeryFinding:
    """
    Сопоставить наименование со структурированным типом.

    Консервативные правила:
    - Нет наименования или типа либо в названии нет явного обозначения типа - not_checked.
    - В атрибуте указан комплект / набор - not_checked (правило PERFUMERY_BUNDLE_SKIPPED).
    - В атрибуте несколько разных типов или тип не распознан - manual_review.
    - В названии несколько разных типов: если атрибут совпадает с первым из них или это
      тип 'духи', встречающийся в названии позже, - ok, иначе - manual_review.
    - Один тип в названии: типы явно не совпадают - warning, совпадают - ok.
    """
    normalized_name = _normalize_text(name)
    normalized_declared = _normalize_text(declared_type)
    declared_set = _find_declared_types(declared_type)
    declared = next(iter(declared_set)) if len(declared_set) == 1 else None

    # Research callers also use this pure helper without the ProductCard adapter.
    if not normalized_name or not normalized_declared:
        return _result(
            CheckStatus.NOT_CHECKED,
            "PERFUMERY_MISSING_INPUT",
            "Недостаточно данных: заполните наименование и тип парфюмерии.",
            None,
            declared,
        )

    types = detect_types_in_name(name)
    detected = types[0] if len(types) == 1 else ("ambiguous" if types else None)

    if _BUNDLE_RE.search(normalized_declared):
        return _result(
            CheckStatus.NOT_CHECKED,
            "PERFUMERY_BUNDLE_SKIPPED",
            f"Тип парфюмерии '{normalized_declared}' обозначает комплект или набор, состав по названию не проверяется.",
            detected,
            normalized_declared,
        )

    if not types:
        return _result(
            CheckStatus.NOT_CHECKED,
            "PERFUMERY_TYPE_NOT_FOUND",
            f"В наименовании '{normalized_name}' не найден маркер типа, заявлен тип '{normalized_declared}'.",
            None,
            declared,
        )

    if len(declared_set) > 1:
        return _result(
            CheckStatus.REVIEW,
            "PERFUMERY_TYPE_MULTIPLE_DECLARED",
            f"В атрибуте указаны типы '{', '.join(sorted(declared_set))}', "
            f"в наименовании найдены типы '{', '.join(types)}', требуется ручная проверка.",
            detected,
            None,
        )

    if declared is None:
        return _result(
            CheckStatus.REVIEW,
            "PERFUMERY_TYPE_UNKNOWN",
            f"Тип атрибута '{normalized_declared}' не распознан, в наименовании найдены типы '{', '.join(types)}'.",
            detected,
            None,
        )

    first = types[0]
    accepted_later = len(types) > 1 and declared in _ACCEPTED_ANYWHERE and declared in types
    if declared == first or (first, declared) in _COMPATIBLE_TYPES or accepted_later:
        return _result(
            CheckStatus.PASS,
            "PERFUMERY_NAME_TYPE_MATCH",
            f"В наименовании найдены типы '{', '.join(types)}', тип атрибута '{declared}' соответствует им.",
            first,
            declared,
        )

    if len(types) > 1:
        return _result(
            CheckStatus.REVIEW,
            "PERFUMERY_TYPE_AMBIGUOUS",
            f"В наименовании найдены типы '{', '.join(types)}', "
            f"тип атрибута '{declared}' не совпадает с первым из них, требуется ручная проверка.",
            "ambiguous",
            declared,
        )

    return _result(
        CheckStatus.WARNING,
        "PERFUMERY_NAME_TYPE_MISMATCH",
        f"Наименование указывает тип '{first}', а в атрибуте указан тип '{declared}'.",
        first,
        declared,
    )
