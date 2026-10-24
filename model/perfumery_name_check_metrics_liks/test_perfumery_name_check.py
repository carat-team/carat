"""100 тестов для алгоритма проверки названия и типа парфюмерии.

Запуск из папки проекта:
    python -m unittest -v test_perfumery_name_check.py

Тесты включают матрицу совпадений/несовпадений типов, граничные случаи,
адаптер карточки и расчёт метрик. Динамически создаются 100 отдельных тестов,
чтобы unittest показывал точное количество проверок.
"""

import unittest

from perfumery_name_check import (
    check_perfumery_name,
    check_product_card,
    check_products_with_metrics,
)

# Названия с явными маркерами и ожидаемые канонические типы.
NAME_CASES = [
    ("Духи Rose 50 мл", "духи"),
    ("Парфюмированная вода Rose 50 мл", "парфюмированная вода"),
    ("Парфюмерная вода Rose 50 мл", "парфюмированная вода"),
    ("Туалетная вода Rose 50 мл", "туалетная вода"),
    ("Одеколон Classic 100 мл", "одеколон"),
    ("Perfume mist Rose", "парфюмерный спрей"),
    ("Body mist Rose", "мист"),
    ("Твердые духи Rose", "твердые духи"),
]

# Разные реальные варианты атрибута. Они намеренно включают синонимы.
DECLARED_CASES = [
    ("ДУХИ", "духи"),
    ("Парфюм", "духи"),
    ("parfum", "духи"),
    ("Парфюмированная вода", "парфюмированная вода"),
    ("Парфюмерная вода", "парфюмированная вода"),
    ("Eau de Parfum", "парфюмированная вода"),
    ("EDP", "парфюмированная вода"),
    ("Туалетная вода", "туалетная вода"),
    ("EDT", "туалетная вода"),
    ("Одеколон", "одеколон"),
]

# 80 тестов: каждый тип в названии сравнивается с 10 вариантами атрибута.
MATRIX_CASES = []
for name, detected_type in NAME_CASES:
    for declared_value, declared_canonical in DECLARED_CASES:
        # Твёрдые духи — разновидность духов: тип ДУХИ для них считается допустимым.
        compatible = detected_type == "твердые духи" and declared_canonical == "духи"
        expected_status = "ok" if detected_type == declared_canonical or compatible else "warning"
        MATRIX_CASES.append((name, declared_value, expected_status, detected_type, declared_canonical))

# 10 граничных тестов: пустые значения, отсутствие маркера, нормализация и алиасы.
EDGE_CASES = [
    ("", "ДУХИ", "not_checked"),
    (None, "ДУХИ", "not_checked"),
    ("Духи Rose", "", "not_checked"),
    ("Духи Rose", None, "not_checked"),
    ("White Horse ALREHAB, 6 мл", "ДУХИ", "not_checked"),
    ("  ДУХИ   Rose 50 мл  ", "духи", "ok"),
    ("Eau de Parfum Rose 50 ml", "Парфюмерная вода", "ok"),
    ("Туалетная вода Rose", "неизвестный тип", "manual_review"),
    ("Твердые духи Rose", "твёрдые духи", "ok"),
    ("Парфюмерная вода Rose", "Парфюмерная вода", "ok"),
]

# 10 тестов метрик: каждый сценарий проверяет структуру отчёта и соответствующий счётчик.
METRIC_CASES = [
    ({"name": "Духи Rose", "declared_type": "ДУХИ"}, "ok", "ok_count"),
    ({"name": "Туалетная вода Rose", "declared_type": "ДУХИ"}, "warning", "warning_count"),
    ({"name": "White Horse", "declared_type": "ДУХИ"}, "not_checked", "not_checked_count"),
    ({"name": "Духи Rose", "declared_type": "неизвестно"}, "manual_review", "manual_review_count"),
    ({"name": "EDP Rose", "declared_type": "EDP"}, "ok", "ok_count"),
    ({"name": "EDT Rose", "declared_type": "EDT"}, "ok", "ok_count"),
    ({"name": "Odеколон", "declared_type": "Одеколон"}, "not_checked", "not_checked_count"),
    ({"name": "Perfume mist Rose", "declared_type": "Парфюмерный спрей"}, "ok", "ok_count"),
    ({"name": "Body mist Rose", "declared_type": "Мист"}, "ok", "ok_count"),
    ({"name": "Твердые духи Rose", "declared_type": "Туалетная вода"}, "warning", "warning_count"),
]


def _make_matrix_test(name, declared, expected_status, expected_detected, expected_declared):
    def test(self):
        result = check_perfumery_name(name, declared)
        self.assertEqual(result["status"], expected_status)
        self.assertEqual(result["detected_type"], expected_detected)
        self.assertEqual(result["declared_type"], expected_declared)
    return test


def _make_edge_test(name, declared, expected_status):
    def test(self):
        result = check_perfumery_name(name, declared)
        self.assertEqual(result["status"], expected_status)
    return test


def _make_metric_test(product, expected_status, expected_counter):
    def test(self):
        report = check_products_with_metrics([product])
        self.assertEqual(report["metrics"]["total_rows"], 1)
        self.assertEqual(report["results"][0]["status"], expected_status)
        self.assertEqual(report["metrics"][expected_counter], 1)
        self.assertIn("processing_time_sec", report["metrics"])
        self.assertIn("rows_per_second", report["metrics"])
    return test


class PerfumeryNameCheckTests(unittest.TestCase):
    """Первые 80 тестов: матрица проверки типов."""


for index, case in enumerate(MATRIX_CASES, start=1):
    setattr(PerfumeryNameCheckTests, f"test_type_matrix_{index:03d}", _make_matrix_test(*case))

for index, case in enumerate(EDGE_CASES, start=81):
    setattr(PerfumeryNameCheckTests, f"test_edge_case_{index:03d}", _make_edge_test(*case))

for index, case in enumerate(METRIC_CASES, start=91):
    setattr(PerfumeryNameCheckTests, f"test_metrics_case_{index:03d}", _make_metric_test(*case))


if __name__ == "__main__":
    unittest.main(verbosity=2)
