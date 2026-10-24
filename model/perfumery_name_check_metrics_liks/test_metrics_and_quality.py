"""Тесты для метрик, оценки качества (evaluation.py) и вспомогательных функций.

Запуск:
    python -m unittest -v test_metrics_and_quality.py
"""

import csv
import tempfile
import unittest
from collections import Counter
from pathlib import Path

import evaluation
from main import build_100_products
from perfumery_name_check import (
    check_perfumery_name,
    check_products_with_metrics,
    detect_type_in_name,
    detect_types_in_name,
    normalize_declared_type,
)

GOLD_PATH = Path(__file__).resolve().parent / "gold_labeled.csv"

# Известные ошибки алгоритма;
KNOWN_ISSUES: set[tuple[str, str]] = set()


class ClassMetricsMathTests(unittest.TestCase):
    """Арифметика precision / recall / F1 на заранее известной матрице ошибок."""

    def test_known_confusion(self):
        confusion = Counter({
            ("warning", "warning"): 8,
            ("ok", "warning"): 2,       # ложные срабатывания
            ("warning", "ok"): 2,       # пропуски
        })
        m = evaluation.class_metrics(confusion, "warning")
        self.assertEqual((m["tp"], m["fp"], m["fn"], m["support"]), (8, 2, 2, 10))
        self.assertAlmostEqual(m["precision"], 0.8)
        self.assertAlmostEqual(m["recall"], 0.8)
        self.assertAlmostEqual(m["f1"], 0.8)

    def test_asymmetric_precision_recall(self):
        confusion = Counter({("warning", "warning"): 3, ("ok", "warning"): 1})
        m = evaluation.class_metrics(confusion, "warning")
        self.assertAlmostEqual(m["precision"], 0.75)
        self.assertAlmostEqual(m["recall"], 1.0)
        self.assertAlmostEqual(m["f1"], round(2 * 0.75 / 1.75, 4))

    def test_absent_class_gives_zeros_without_division_error(self):
        m = evaluation.class_metrics(Counter(), "manual_review")
        self.assertEqual((m["precision"], m["recall"], m["f1"], m["support"]), (0.0, 0.0, 0.0, 0))


class EvaluateTests(unittest.TestCase):
    def test_perfect_prediction(self):
        rows = [
            {"name": "Духи Rose", "declared_type": "ДУХИ", "expected_status": "ok"},
            {"name": "Туалетная вода Rose", "declared_type": "ДУХИ", "expected_status": "warning"},
            {"name": "White Horse", "declared_type": "ДУХИ", "expected_status": "not_checked"},
        ]
        report = evaluation.evaluate(rows)
        self.assertEqual(report["total"], 3)
        self.assertEqual(report["accuracy"], 1.0)
        self.assertEqual(report["mistakes"], [])
        self.assertEqual(report["per_class"]["warning"]["f1"], 1.0)

    def test_mistake_is_reported(self):
        rows = [{"name": "Духи Rose", "declared_type": "ДУХИ", "expected_status": "warning"}]
        report = evaluation.evaluate(rows)
        self.assertEqual(report["accuracy"], 0.0)
        self.assertEqual(len(report["mistakes"]), 1)
        self.assertEqual(report["mistakes"][0]["expected"], "warning")
        self.assertEqual(report["mistakes"][0]["predicted"], "ok")
        self.assertEqual(report["confusion_matrix"]["warning"]["ok"], 1)

    def test_empty_input(self):
        report = evaluation.evaluate([])
        self.assertEqual(report["total"], 0)
        self.assertEqual(report["accuracy"], 0.0)
        self.assertEqual(report["macro_f1"], 0.0)


class LoadCsvTests(unittest.TestCase):
    def _write(self, rows):
        tmp = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8-sig", newline="")
        csv.writer(tmp).writerows(rows)
        tmp.close()
        self.addCleanup(Path(tmp.name).unlink)
        return tmp.name

    def test_roundtrip_with_comma_in_name(self):
        path = self._write([
            ["name", "declared_type", "expected_status"],
            ["White Horse ALREHAB, 6 мл", "ДУХИ", "not_checked"],
        ])
        rows = evaluation.load_labeled_csv(path)
        self.assertEqual(rows[0]["name"], "White Horse ALREHAB, 6 мл")

    def test_invalid_status_raises(self):
        path = self._write([
            ["name", "declared_type", "expected_status"],
            ["Духи Rose", "ДУХИ", "fine"],
        ])
        with self.assertRaises(ValueError):
            evaluation.load_labeled_csv(path)

    def test_gold_file_is_valid(self):
        rows = evaluation.load_labeled_csv(GOLD_PATH)
        self.assertGreaterEqual(len(rows), 30)
        self.assertEqual({r["expected_status"] for r in rows}, set(evaluation.STATUSES))


class GoldRegressionTests(unittest.TestCase):
    """Каждая размеченная карточка — отдельная проверка. Известные ошибки вынесены ниже."""

    def test_gold_cases(self):
        for row in evaluation.load_labeled_csv(GOLD_PATH):
            if (row["name"], row["declared_type"]) in KNOWN_ISSUES:
                continue
            with self.subTest(name=row["name"], declared=row["declared_type"]):
                result = check_perfumery_name(row["name"], row["declared_type"])
                self.assertEqual(result["status"], row["expected_status"])

    def test_quality_floor(self):
        report = evaluation.evaluate(evaluation.load_labeled_csv(GOLD_PATH))
        self.assertGreaterEqual(report["accuracy"], 0.9)
        self.assertEqual(report["per_class"]["warning"]["recall"], 1.0)  # ни одного пропуска


class FixedIssuesTests(unittest.TestCase):
    """Ошибки, найденные оценкой качества и на реальном каталоге, и их исправления."""

    def test_parfum_de_toilette_is_toilet_water(self):
        self.assertEqual(check_perfumery_name("Parfum de Toilette Rose", "Туалетная вода")["status"], "ok")

    def test_multi_value_declared_type_needs_review(self):
        r = check_perfumery_name("Туалетная вода Rose", "EDT; ДУХИ")
        self.assertEqual((r["status"], r["rule"]), ("manual_review", "PERFUMERY_TYPE_MULTIPLE_DECLARED"))

    def test_multi_value_declared_with_slash(self):
        self.assertEqual(check_perfumery_name("Духи Rose", "Духи/Парфюмерная вода")["status"], "manual_review")

    def test_conflicting_markers_declared_not_first_needs_review(self):
        r = check_perfumery_name("Rose EDP/EDT набор", "EDT")
        self.assertEqual((r["status"], r["rule"]), ("manual_review", "PERFUMERY_TYPE_AMBIGUOUS"))

    def test_conflicting_markers_declared_equals_first_is_ok(self):
        self.assertEqual(check_perfumery_name("Rose EDT/EDP набор", "EDT")["status"], "ok")

    def test_real_catalog_pattern_edp_then_dukhi_is_ok(self):
        # Самый частый паттерн реального каталога: «… Eau De Parfum духи 15мл» при типе ДУХИ.
        r = check_perfumery_name("Devotion Eau De Parfum духи 15мл", "ДУХИ")
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["detected_type"], "парфюмированная вода")

    def test_dukhi_later_in_name_is_accepted_only_for_attribute_dukhi(self):
        self.assertEqual(check_perfumery_name("Rose EDT духи 15мл", "ДУХИ")["status"], "ok")
        # для другого типа атрибута несовпадение с первым маркером по-прежнему требует проверки
        self.assertEqual(check_perfumery_name("Rose EDP духи 10 мл", "Туалетная вода")["status"], "manual_review")
        self.assertEqual(check_perfumery_name("Духи Rose EDP", "Парфюмированная вода")["status"], "manual_review")

    def test_second_non_dukhi_marker_is_not_accepted(self):
        # EDT стоит вторым — это по-прежнему повод для ручной проверки
        self.assertEqual(check_perfumery_name("Rose EDP/EDT набор", "EDT")["status"], "manual_review")

    def test_solid_perfume_is_compatible_with_perfume(self):
        self.assertEqual(check_perfumery_name("Твердые духи Rose", "ДУХИ")["status"], "ok")
        self.assertEqual(check_perfumery_name("Твёрдые духи Rose", "Парфюм")["status"], "ok")

    def test_solid_perfume_compatibility_is_one_way_and_not_universal(self):
        self.assertEqual(check_perfumery_name("Духи Rose", "Твёрдые духи")["status"], "warning")
        self.assertEqual(check_perfumery_name("Твердые духи Rose", "Туалетная вода")["status"], "warning")


class HelperFunctionTests(unittest.TestCase):
    def test_normalize_declared_type_synonyms(self):
        self.assertEqual(normalize_declared_type("  Eau  de  Toilette "), "туалетная вода")
        self.assertEqual(normalize_declared_type("ТВЁРДЫЕ ДУХИ"), "твердые духи")
        self.assertIsNone(normalize_declared_type("что-то непонятное"))
        self.assertIsNone(normalize_declared_type(None))
        self.assertIsNone(normalize_declared_type(float("nan")))

    def test_detect_type_in_name(self):
        self.assertEqual(detect_type_in_name("Rose EDT 50 ml"), "туалетная вода")
        self.assertEqual(detect_type_in_name("Perfume mist Rose"), "парфюмерный спрей")
        self.assertIsNone(detect_type_in_name("Rose 50 ml"))
        self.assertIsNone(detect_type_in_name(None))

    def test_nested_marker_is_not_counted_twice(self):
        # «parfum» внутри «eau de parfum» — это не отдельный тип «духи»
        self.assertEqual(detect_types_in_name("Rose Eau de Parfum 50 ml"), ["парфюмированная вода"])
        self.assertEqual(detect_types_in_name("Твердые духи Rose"), ["твердые духи"])

    def test_types_are_ordered_by_position(self):
        self.assertEqual(detect_types_in_name("Rose EDP / EDT"), ["парфюмированная вода", "туалетная вода"])
        self.assertEqual(detect_type_in_name("Rose EDP / EDT"), "ambiguous")

    def test_declared_type_variants_from_real_catalog(self):
        self.assertEqual(normalize_declared_type("ДЕТСКИЕ ДУХИ"), "духи")
        self.assertEqual(normalize_declared_type("Натуральные твердые духи"), "твердые духи")
        self.assertEqual(normalize_declared_type("ПАРФЮМЕРНАЯ ВОДА"), "парфюмированная вода")
        self.assertIsNone(normalize_declared_type("КОМПЛЕКТ"))  # значения вне списка типов не угадываются
        self.assertIsNone(normalize_declared_type("EDT; ДУХИ"))  # несколько типов сразу

    def test_marker_must_be_whole_word(self):
        self.assertIsNone(detect_type_in_name("Redpoint 50 ml"))  # «edp» внутри слова не считается

    def test_nan_and_none_inputs_are_not_checked(self):
        self.assertEqual(check_perfumery_name(float("nan"), "ДУХИ")["status"], "not_checked")
        self.assertEqual(check_perfumery_name("Духи Rose", float("nan"))["status"], "not_checked")

    def test_case_and_nbsp_are_ignored(self):
        self.assertEqual(check_perfumery_name("ДУХИ\u00a0Rose", "духи")["status"], "ok")

    def test_result_has_all_keys(self):
        result = check_perfumery_name("Духи Rose", "ДУХИ")
        self.assertEqual(set(result), {"status", "rule", "message", "detected_type", "declared_type"})


class BatchMetricsTests(unittest.TestCase):
    def test_empty_batch(self):
        metrics = check_products_with_metrics([])["metrics"]
        self.assertEqual(metrics["total_rows"], 0)
        self.assertEqual(metrics["warning_rate_percent"], 0.0)
        self.assertEqual(metrics["coverage_rate_percent"], 0.0)
        self.assertEqual(metrics["rules_count"], {})

    def test_counts_sum_to_total(self):
        metrics = check_products_with_metrics(build_100_products())["metrics"]
        parts = sum(metrics[k] for k in ("ok_count", "warning_count", "manual_review_count", "not_checked_count"))
        self.assertEqual(parts, metrics["total_rows"])

    def test_percentages_are_exact(self):
        products = [
            {"name": "Духи Rose", "declared_type": "ДУХИ"},                 # ok
            {"name": "Туалетная вода Rose", "declared_type": "ДУХИ"},       # warning
            {"name": "White Horse", "declared_type": "ДУХИ"},               # not_checked
            {"name": "Духи Rose", "declared_type": "неизвестно"},           # manual_review
        ]
        metrics = check_products_with_metrics(products)["metrics"]
        self.assertEqual(metrics["warning_rate_percent"], 25.0)
        self.assertEqual(metrics["coverage_rate_percent"], 50.0)

    def test_rules_count(self):
        products = [
            {"name": "Духи Rose", "declared_type": "ДУХИ"},
            {"name": "Духи Amber", "declared_type": "ДУХИ"},
            {"name": "Туалетная вода Rose", "declared_type": "ДУХИ"},
        ]
        rules = check_products_with_metrics(products)["metrics"]["rules_count"]
        self.assertEqual(rules, {"PERFUMERY_NAME_TYPE_MATCH": 2, "PERFUMERY_NAME_TYPE_MISMATCH": 1})

    def test_card_with_excel_style_headers(self):
        card = {"Полное наименование товара (2478)": "Духи Rose", "Тип парфюмерии (1034)": "ДУХИ"}
        report = check_products_with_metrics([card])
        self.assertEqual(report["results"][0]["status"], "ok")

    def test_demo_set_is_the_documented_100(self):
        products = build_100_products()
        self.assertEqual(len(products), 100)
        self.assertEqual(len({p["test_id"] for p in products}), 100)
        metrics = check_products_with_metrics(products)["metrics"]
        self.assertEqual(
            (metrics["ok_count"], metrics["warning_count"], metrics["manual_review_count"], metrics["not_checked_count"]),
            (70, 10, 5, 15),
        )
        self.assertEqual(metrics["warning_rate_percent"], 10.0)
        self.assertEqual(metrics["coverage_rate_percent"], 80.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
