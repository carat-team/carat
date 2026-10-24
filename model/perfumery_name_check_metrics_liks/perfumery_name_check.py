"""
Алгоритмическая проверка: «Наименование товара не соответствует типу парфюмерии».

Проверка сопоставляет явные обозначения типа парфюмерии в наименовании товара 
со структурированным атрибутом «Тип парфюмерии».

Результат содержит:
    status: "ok" | "warning" | "manual_review" | "not_checked"
    rule: постоянный идентификатор правила или None
    message: пояснение для проверяющего
    detected_type: нормализованный тип, определённый по наименованию, или None
    declared_type: нормализованный тип из атрибута или None
"""

from __future__ import annotations

import re
from time import perf_counter
from collections import Counter
from typing import Any, Iterable, Mapping

# Сначала следует проверять более длинные и точные выражения.
# Справочник типов парфюмерии
# Канонические значения должны соответствовать значениям в исходном каталоге.
_TYPE_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "парфюмированная вода",
        (
            r"\bпарфюмированн(?:ая|ой|ую|ую|ые|ых|ыми)\s+вод[аыуеой]\b",
            r"\beau\s+de\s+parfum\b",
            r"\bedp\b",
            r"\bпарфвода\b",
        ),
    ),
    (
        "туалетная вода",
        (
            r"\bтуалетн(?:ая|ой|ую|ые|ых|ыми)\s+вод[аыуеой]\b",
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
    ("парфюмированная вода", (r"\bпарфюмерн(?:ая|ой|ую|ые|ых|ыми)\s+вод[аыуеой]\b",)),
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


# Приводит входное значение к единому виду: убирает лишние пробелы и знаки,
# заменяет «ё» на «е» и безопасно обрабатывает пустые значения и NaN.
def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    # Обрабатывает NaN без необходимости подключать pandas.
    try:
        if value != value:
            return ""
    except Exception:
        pass
    text = str(value).lower().replace("ё", "е")
    text = text.replace("ё", "е")
    text = re.sub(r"[\u00a0]+", " ", text)
    text = re.sub(r"[_/|]+", " ", text)
    text = re.sub(r"[^\w\s-]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


# Пары (тип в названии, тип в атрибуте), которые считаются совместимыми, хотя типы
# не равны. Твёрдые духи — разновидность духов, отдельного значения для них в
# справочнике «Тип парфюмерии» нет. Чтобы отключить правило, оставьте множество пустым.
_COMPATIBLE_TYPES = frozenset({("твердые духи", "духи")})

# Типы атрибута, которые допустимы, если слово встречается в названии не первым.
# «Духи» часто стоит в конце названия как формат («… Eau de Parfum духи 15мл»), поэтому
# при атрибуте ДУХИ такие карточки считаются совпадением. Чтобы отключить правило,
# оставьте множество пустым.
_ACCEPTED_ANYWHERE = frozenset({"духи"})

_BUNDLE_DECLARED_TYPES = frozenset({"комплект", "набор"})

_SORTED_ALIASES = sorted(_TYPE_ALIASES.items(), key=lambda item: len(item[0]), reverse=True)


# Находит в значении атрибута все известные типы. Более длинные синонимы проверяются
# первыми и «съедают» своё место, поэтому «твёрдые духи» не считаются ещё и «духами».
def _find_declared_types(value: Any) -> set[str]:
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
# распознано или содержит несколько разных типов («EDT; ДУХИ») — возвращает None.
def normalize_declared_type(value: Any) -> str | None:
    found = _find_declared_types(value)
    return next(iter(found)) if len(found) == 1 else None


# Ищет в названии все обозначения типов. Если одно обозначение лежит внутри более
# длинного («parfum» в «eau de parfum»), учитывается только длинное.
# Возвращает канонические типы без повторов в порядке появления в названии.
def detect_types_in_name(name: Any) -> list[str]:
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


# Тип по названию: None — маркера нет, \"ambiguous\" — в названии несколько разных
# типов, иначе — канонический тип.
def detect_type_in_name(name: Any) -> str | None:
    types = detect_types_in_name(name)
    if not types:
        return None
    return types[0] if len(types) == 1 else "ambiguous"


def _result(status: str, rule: str | None, message: str, detected: str | None, declared: str | None) -> dict[str, Any]:
    return {
        "status": status,
        "rule": rule,
        "message": message,
        "detected_type": detected,
        "declared_type": declared,
    }


# Сравнивает распознанный в названии тип с типом атрибута и возвращает статус,
# идентификатор правила и пояснение для проверки карточки.
def check_perfumery_name(name: Any, declared_type: Any) -> dict[str, Any]:
    """
    Сопоставить наименование со структурированным типом.

    Консервативные правила:
    - Нет наименования или типа либо в названии нет явного обозначения типа — not_checked.
    - В атрибуте несколько разных типов или тип не распознан — manual_review.
    - В названии несколько разных типов: если атрибут совпадает с первым из них или это
      тип «духи», встречающийся в названии позже, — ok, иначе — manual_review.
    - Один тип в названии: типы явно не совпадают — warning, совпадают — ok.
    """
    normalized_name = _normalize_text(name)
    normalized_declared = _normalize_text(declared_type)
    declared_set = _find_declared_types(declared_type)
    declared = next(iter(declared_set)) if len(declared_set) == 1 else None

    if not normalized_name or not normalized_declared:
        return _result(
            "not_checked", None,
            "Недостаточно данных: заполните наименование и тип парфюмерии.",
            None, declared,
        )

    types = detect_types_in_name(name)
    if not types:
        return _result(
            "not_checked", None,
            "В наименовании не найден явный маркер типа парфюмерии; автоматический вывод не делается.",
            None, declared,
        )

    detected = types[0] if len(types) == 1 else "ambiguous"

    if normalized_declared in _BUNDLE_DECLARED_TYPES:
        return _result(
            "ok", "PERFUMERY_BUNDLE_TYPE_MATCH",
            "Карточка обозначена как комплект, содержащий парфюмерию.",
            detected, normalized_declared,
        )

    if len(declared_set) > 1:
        return _result(
            "manual_review", "PERFUMERY_TYPE_MULTIPLE_DECLARED",
            "В атрибуте «Тип парфюмерии» указано несколько разных типов. Требуется ручная проверка.",
            detected, None,
        )

    if declared is None:
        return _result(
            "manual_review", "PERFUMERY_TYPE_UNKNOWN",
            "Не удалось распознать значение атрибута «Тип парфюмерии». Требуется проверить справочник типов.",
            detected, None,
        )

    first = types[0]
    accepted_later = len(types) > 1 and declared in _ACCEPTED_ANYWHERE and declared in types
    if declared == first or (first, declared) in _COMPATIBLE_TYPES or accepted_later:
        return _result(
            "ok", "PERFUMERY_NAME_TYPE_MATCH",
            "Тип парфюмерии в наименовании соответствует значению атрибута.",
            first, declared,
        )

    if len(types) > 1:
        return _result(
            "manual_review", "PERFUMERY_TYPE_AMBIGUOUS",
            "В наименовании указано несколько разных типов парфюмерии, и атрибут не совпадает с первым из них. Требуется ручная проверка.",
            "ambiguous", declared,
        )

    return _result(
        "warning", "PERFUMERY_NAME_TYPE_MISMATCH",
        f"Наименование указывает тип «{first}», а в атрибуте указан тип «{declared}».",
        first, declared,
    )


# Извлекает название и тип из словаря карточки по известным именам полей,
# затем передаёт эти значения в основную функцию проверки.
def check_product_card(card: Mapping[str, Any]) -> dict[str, Any]:
    """
    Вспомогательная функция для словаря с данными карточки товара.

    В исходном файле Excel используются заголовки, например:
        - "Полное наименование товара (2478)"
        - "Тип парфюмерии (1034)"

    Поддерживаются как точные, так и распространённые сокращённые названия полей.
    """
    name_keys = (
        "Полное наименование товара (2478)",
        "Полное наименование товара",
        "name",
        "product_name",
        "title",
    )
    type_keys = (
        "Тип парфюмерии (1034)",
        "Тип парфюмерии",
        "perfumery_type",
        "declared_type",
    )

    name = next((card[key] for key in name_keys if key in card), None)
    declared_type = next((card[key] for key in type_keys if key in card), None)
    return check_perfumery_name(name, declared_type)


def check_products_with_metrics(
    products: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Проверить набор карточек и вернуть результаты вместе с метриками.

    Каждый элемент products — словарь, который поддерживает check_product_card(),
    например {"name": "Туалетная вода Rose", "declared_type": "ДУХИ"}.
    """
    started = perf_counter()
    results = [check_product_card(product) for product in products]
    elapsed = perf_counter() - started

    counts = Counter(result["status"] for result in results)
    total = len(results)
    automatic = counts["ok"] + counts["warning"]

    def percentage(value: int, denominator: int) -> float:
        return round(value / denominator * 100, 2) if denominator else 0.0

    metrics = {
        "total_rows": total,
        "ok_count": counts["ok"],
        "warning_count": counts["warning"],
        "manual_review_count": counts["manual_review"],
        "not_checked_count": counts["not_checked"],
        "warning_rate_percent": percentage(counts["warning"], total),
        "coverage_rate_percent": percentage(automatic, total),
        "processing_time_sec": round(elapsed, 6),
        "rows_per_second": round(total / elapsed, 2) if elapsed > 0 else 0.0,
        "rules_count": dict(Counter(
            result["rule"] for result in results if result.get("rule") is not None
        )),
    }
    return {"results": results, "metrics": metrics}
