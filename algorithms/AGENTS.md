# algorithms/AGENTS.md

Library of product-card checks. Read the root `AGENTS.md` first; this file adds rules for `algorithms/` only.
Package `carat_algorithms`, Python 3.12, uv, `src/` layout. Human-facing explanation and a full check example:
`README.md`.

## Purity

- No HTTP, gRPC, database, queue, web framework or network access.
- Never import `backend`, `model`, `fastapi`, `sqlalchemy`, `psycopg`, `grpc`.
- File I/O only for package data (`importlib.resources`) and model weights from a `weights_directory: Path`
  passed by the caller. Never hardcode a weights path.
- No global mutable state, no clocks, no unseeded randomness. Same input -> same output.
- A check never raises on bad or missing input: return `NOT_CHECKED` or `REVIEW`. The backend runner turns
  unexpected exceptions into `ERROR`.
- Never log card contents, field values or photos. Log the check id and reason code at most.

## Layout

- `core/`: ProductCard, CheckResult, CheckStatus, Check protocol, `registry.py`.
- `text/`, `identifiers/`, `vision/` (vision needs the `[vision]` extra): one subpackage per check.
- `tests/` mirrors `src/`, data in `tests/fixtures/`. `scripts/` is dev tooling, never imported by `src/`.
- Shared helpers move into `core/` only once two checks need them.

## Dependencies

- Core group: pydantic (add rapidfuzz when a check needs it). `[vision]`: pillow, zxing-cpp (plus
  opencv-python-headless, numpy when a check needs them). `[ml]`: easyocr on CPU torch
  (approved; torch comes from the explicit `pytorch-cpu` index).
- `uv add <pkg>` / `uv add --optional <extra> <pkg>`; commit `uv.lock` with `pyproject.toml`.
- Import heavy libraries inside the module that uses them, never in `core/` or a package `__init__`.
  `import carat_algorithms.core` must work with the core group only.
- `opencv-python` (GUI build) is forbidden. Torch-based dependencies need approval.

## Adding a check

1. `src/carat_algorithms/<area>/<check_name>/__init__.py` exports the check class.
2. Implement `Check`: `check_id: str` (stable snake_case), `algorithm_version: int`, `run(card) -> CheckResult`.
3. Every result sets all fields:
   - `reason_code`: `UPPER_SNAKE_CASE`, prefixed with the check name (`VOLUME_MISMATCH`).
   - `explanation`: one Russian sentence naming the compared values ("Объём в названии 50 мл, в атрибуте 100 мл").
   - `field_refs`: API field names the verdict uses (`("fullName", "volume")`).
   - `algorithm_version`: the check's integer version.
4. Bump `algorithm_version` by 1 on any change that can alter a result (rule, threshold, model, preprocessing).
5. Register in `core/registry.py`; unregistered checks do not run.
6. Tests, then `just algorithms check`.
7. PR description: Taiga link and requirement number from `docs/requirements.md`.

## Style

- Quotes in code, comments and explanations are plain `"` or `'`, never `«»`.

## Statuses

- `PASS` rule satisfied. `WARNING` likely problem. `REVIEW` cannot decide. `NOT_CHECKED` precondition missing.
  `ERROR` is set only by the backend runner; checks never return it.
- `None` field -> `NOT_CHECKED`. Empty string where text is required -> a finding, not `NOT_CHECKED`.
- Prefer `REVIEW` over an uncertain `WARNING`.
- No new statuses, verdict enums or 0-1 scores.

## Tests

- pytest, `@pytest.mark.parametrize` for rule tables, readable ids, one behaviour per case.
- Real ЧЗ catalog mistakes become named regression cases (`test_brand_inside_name_real_case_0412`).
- Only committed files; images under 100 KB or generated in the test.
- Each check: at least one `NOT_CHECKED` case and one failing-card case.
- Accuracy metrics go to `scripts/` or `model/`, not `tests/`.
- Never delete or weaken a test to make a change pass.

## Model-based checks

- Never commit weights. Document source URL, filename, checksum and target path in `README.md`.
- Load once, lazily, behind a lock; never at import time.
- Model name, preprocessing and threshold are part of `algorithm_version`.
- A model score is not a calibrated probability; never show it as a percentage.
- Training and evaluation live in `model/`; `algorithms/` only runs inference.
