"""Оценка качества проверки на размеченной выборке: accuracy, precision, recall, F1.

Формат CSV (UTF-8): name, declared_type, expected_status
expected_status — ответ, который ожидает эксперт: ok | warning | manual_review | not_checked.

Запуск:
    python evaluation.py [путь_к_csv] [--out отчёт.json]
        по умолчанию читается gold_labeled.csv (лежит рядом со скриптом);
        отчёт для другого CSV не перезаписывает quality_report.json.

"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

from perfumery_name_check import check_perfumery_name

STATUSES = ("ok", "warning", "manual_review", "not_checked")


def load_labeled_csv(path: str | Path) -> list[dict[str, str]]:
    """Читает размеченный CSV и проверяет, что expected_status допустим."""
    with Path(path).open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    for line_no, row in enumerate(rows, start=2):
        status = row.get("expected_status")
        if status not in STATUSES:
            raise ValueError(f"Строка {line_no}: неизвестный expected_status {status!r}")
    return rows


def _safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def class_metrics(confusion: Mapping[tuple[str, str], int], label: str) -> dict[str, Any]:
    """Precision/recall/F1 для одного статуса. Ключ confusion: (ожидали, получили)."""
    tp = confusion.get((label, label), 0)
    fp = sum(v for (exp, pred), v in confusion.items() if pred == label and exp != label)
    fn = sum(v for (exp, pred), v in confusion.items() if exp == label and pred != label)
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    f1 = _safe_div(2 * precision * recall, precision + recall)
    return {
        "tp": tp, "fp": fp, "fn": fn, "support": tp + fn,
        "precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4),
    }


def evaluate(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Прогоняет алгоритм по размеченным строкам и считает метрики качества."""
    confusion: Counter[tuple[str, str]] = Counter()
    mistakes: list[dict[str, Any]] = []
    total = 0
    for row in rows:
        total += 1
        result = check_perfumery_name(row["name"], row["declared_type"])
        expected, predicted = row["expected_status"], result["status"]
        confusion[(expected, predicted)] += 1
        if expected != predicted:
            mistakes.append({
                "name": row["name"], "declared_type": row["declared_type"],
                "expected": expected, "predicted": predicted, "rule": result["rule"],
            })

    correct = sum(v for (exp, pred), v in confusion.items() if exp == pred)
    per_class = {s: class_metrics(confusion, s) for s in STATUSES}
    present = [m["f1"] for m in per_class.values() if m["support"] > 0]
    matrix = {e: {p: confusion.get((e, p), 0) for p in STATUSES} for e in STATUSES}
    return {
        "total": total,
        "accuracy": round(_safe_div(correct, total), 4),
        "macro_f1": round(_safe_div(sum(present), len(present)), 4),
        "per_class": per_class,
        "confusion_matrix": matrix,  # строки — ожидалось, столбцы — получено
        "mistakes": mistakes,
    }


def print_report(report: Mapping[str, Any]) -> None:
    print(f"Размеченных карточек: {report['total']}")
    print(f"Accuracy: {report['accuracy']:.2%}   Macro-F1: {report['macro_f1']:.2%}\n")
    print(f"{'статус':<15}{'precision':>10}{'recall':>9}{'F1':>8}{'support':>9}")
    for status, m in report["per_class"].items():
        print(f"{status:<15}{m['precision']:>10.2%}{m['recall']:>9.2%}{m['f1']:>8.2%}{m['support']:>9}")
    print("\nМатрица ошибок (строки — ожидалось, столбцы — получено):")
    print(f"{'':<15}" + "".join(f"{s:>15}" for s in STATUSES))
    for exp, row in report["confusion_matrix"].items():
        print(f"{exp:<15}" + "".join(f"{row[s]:>15}" for s in STATUSES))
    if report["mistakes"]:
        print(f"\nРасхождения ({len(report['mistakes'])}):")
        for m in report["mistakes"]:
            print(f"  «{m['name']}» | «{m['declared_type']}» — ожидали {m['expected']}, получили {m['predicted']}")


def main(argv: list[str] | None = None) -> None:
    base = Path(__file__).resolve().parent
    default_csv = base / "gold_labeled.csv"

    parser = argparse.ArgumentParser(description="Оценка качества проверки на размеченной выборке.")
    parser.add_argument("csv", nargs="?", type=Path, default=default_csv,
                        help="размеченный CSV (по умолчанию gold_labeled.csv рядом со скриптом)")
    parser.add_argument("--out", type=Path, default=None,
                        help="куда сохранить JSON-отчёт (по умолчанию: quality_report.json для "
                             "gold_labeled.csv, иначе <имя_csv>_quality_report.json рядом с CSV)")
    args = parser.parse_args(argv)

    if not args.csv.is_file():
        parser.error(f"файл разметки не найден: {args.csv}")

    if args.out is not None:
        out = args.out
    elif args.csv.resolve() == default_csv.resolve():
        out = base / "quality_report.json"
    else:
        out = args.csv.with_name(f"{args.csv.stem}_quality_report.json")

    report = evaluate(load_labeled_csv(args.csv))
    print_report(report)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nJSON-отчёт сохранён: {out}")


if __name__ == "__main__":
    main()
