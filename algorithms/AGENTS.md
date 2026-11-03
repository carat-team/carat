# algorithms/AGENTS.md

Library of product-card checks; adds to the root `AGENTS.md`. Package `carat_algorithms`, Python 3.12, uv, `src/`
layout. Human guide with a full example: `README.md` and `docs/how-to-add-a-check.md`.

## Purity

- No HTTP, gRPC, database, queue, web framework or network access. Never import `backend`, `model`, `fastapi`,
  `sqlalchemy`, `psycopg`, `grpc`.
- File I/O only for package data (`importlib.resources`) and weights under the `weights_dir: Path` from the caller.
  A model family reads `<weights_dir>/<family>/`, named by a `WEIGHTS_SUBDIRECTORY` constant next to the model
  code. Never hardcode a weights path.
- No global mutable state, clocks or unseeded randomness: same input -> same output.
- A check never raises on bad or missing input; it returns `NOT_CHECKED` or `REVIEW`. The backend runner turns
  unexpected exceptions into `ERROR`.
- Never log card contents, field values or photos; check id and reason code at most.

## Layout

- `core/`: `ProductCard`, `CheckResult`, `CheckStatus`, `Check` protocol, `registry.py`.
- `text/`, `identifiers/`, `vision/`: one subpackage per check.
- `tests/` mirrors `src/`, data in `tests/fixtures/`. `scripts/` is dev tooling, never imported by `src/`.
- Shared helpers move into `core/` only once two checks need them.

## Dependencies

- Core: pydantic. `[vision]`: pillow, zxing-cpp. `[ml]`: easyocr on CPU torch from the explicit `pytorch-cpu` index.
- `uv add <pkg>` or `uv add --optional <extra> <pkg>`.
- Heavy libraries are imported inside the module that uses them, never in `core/` or a package `__init__`;
  `import carat_algorithms.core` works with the core group only.
- `opencv-python` (GUI build) is forbidden; use `opencv-python-headless`. New torch-based dependencies need approval.

## Adding a check

1. `src/carat_algorithms/<area>/<check_name>/__init__.py` exports the check class.
2. Implement `Check`: `check_id` (stable snake_case), `algorithm_version: int`, `run(card) -> CheckResult`.
3. Every result sets:
   - `reason_code`: `UPPER_SNAKE_CASE` with the check prefix (`VOLUME_MISMATCH`);
   - `explanation`: one Russian sentence with the compared values ("Объём в названии 50 мл, в атрибуте 100 мл");
   - `field_refs`: API field names (`("fullName", "volume")`);
   - `algorithm_version`.
4. Bump `algorithm_version` by 1 on any change that can alter a result (rule, threshold, model, preprocessing).
5. Register in `core/registry.py` (import inside `get_checks()`); unregistered checks do not run.
6. Tests, then `just algorithms check`. PR description: Taiga link and the requirement from `docs/requirements.md`.

## Statuses

- `PASS` satisfied, `WARNING` likely problem, `REVIEW` cannot decide, `NOT_CHECKED` precondition missing. `ERROR`
  comes only from the backend runner.
- `None` field -> `NOT_CHECKED`. An empty string where text is required is a finding, not `NOT_CHECKED`.
- Prefer `REVIEW` over an uncertain `WARNING`. No new statuses, verdict enums or 0-1 scores.

## Tests

- pytest, `@pytest.mark.parametrize` for rule tables with readable ids, one behaviour per case.
- Each check: at least one `NOT_CHECKED` case and one failing-card case. Real ЧЗ catalog mistakes become named
  regression cases.
- Only committed files; images under 100 KB or generated in the test.
- Accuracy metrics go to `scripts/` or `model/`, not `tests/`.

## Model-based checks

- Never commit weights; document source URL, filename, checksum and target path in `README.md`.
- Load once, lazily, behind a lock; never at import time.
- Model name, preprocessing and threshold are part of `algorithm_version`.
- A model score is not a calibrated probability; never show it as a percentage.
- Training and evaluation live in `model/`; `algorithms/` only runs inference.
