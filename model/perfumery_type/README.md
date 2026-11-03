# Perfumery type research and evaluation

Runtime check: carat_algorithms.text.perfumery_type.PerfumeryTypeCheck, requirement R3, Taiga #29.
Rules and the shared registry live in algorithms/src; backend never imports this research directory.

The scripts preserve the original experiment, batch reporting and historical CSV labels
(ok, warning, manual_review, not_checked). Production returns the shared uppercase CheckStatus values.
The Check adapter distinguishes absent fields from empty entered strings.

From the repository root:
- uv run --project algorithms --group evaluation python -m unittest discover -s model/perfumery_type -p test_perfumery_name_check.py
- uv run --project algorithms --group evaluation python model/perfumery_type/evaluation.py PATH_TO_LABELED_CSV --out REPORT.json
- uv run --project algorithms --group evaluation python model/perfumery_type/check_catalog.py PATH_TO_CATALOG.xlsx

Labeled CSV columns: name, declared_type, expected_status (historical labels above).
Catalog and gold_labeled.csv are not bundled; obtain the approved source from the task owners.
GoldRegressionTests and test_gold_file_is_valid require that external labeled file beside the scripts.
No gold accuracy measurement is claimed by the self-contained algorithms unit tests.
