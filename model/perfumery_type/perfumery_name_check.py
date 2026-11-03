"""Research-only compatibility with historical CSV labels; production uses CheckStatus."""

from collections import Counter
from collections.abc import Iterable, Mapping
from time import perf_counter
from typing import Any

from carat_algorithms.core import CheckStatus
from carat_algorithms.text.perfumery_type.rules import (
    check_perfumery_name as _check_perfumery_name,
    detect_type_in_name,
    detect_types_in_name,
    normalize_declared_type,
)

_RESEARCH_LABELS = {
    CheckStatus.PASS: "ok",
    CheckStatus.WARNING: "warning",
    CheckStatus.REVIEW: "manual_review",
    CheckStatus.NOT_CHECKED: "not_checked",
}


def check_perfumery_name(name: object, declared_type: object) -> dict[str, Any]:
    result: dict[str, Any] = dict(_check_perfumery_name(name, declared_type))
    result["status"] = _RESEARCH_LABELS[result["status"]]
    if result["rule"] in ("PERFUMERY_MISSING_INPUT", "PERFUMERY_TYPE_NOT_FOUND"):
        result["rule"] = None
    return result


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
        # Доля карточек, по которым алгоритм принял решение (ok + warning).
        # Это НЕ качество и не «покрытие» корректных карточек.
        "auto_decision_rate_percent": percentage(automatic, total),
        # Устаревшее имя, оставлено для обратной совместимости.
        "coverage_rate_percent": percentage(automatic, total),
        "processing_time_sec": round(elapsed, 6),
        "rows_per_second": round(total / elapsed, 2) if elapsed > 0 else 0.0,
        "rules_count": dict(Counter(
            result["rule"] for result in results if result.get("rule") is not None
        )),
    }
    return {"results": results, "metrics": metrics}
