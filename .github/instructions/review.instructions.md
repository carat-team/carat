---
applyTo: "**"
excludeAgent: "coding-agent"
---

# Copilot code review instructions

The canonical review rules are in `REVIEW.md` at the repository root; project rules are in the
root `AGENTS.md`. This file repeats the essentials because Copilot does not read the per-service
`AGENTS.md` files. Keep it in sync with `REVIEW.md`.

## Blocking

- Secrets, `.env` files, credentials.
- Model weights, datasets, CSV/NPY dumps, archives or generated code in the diff.
- Check logic (rules, parsers, text comparison, image analysis, model calls) in `backend/`; it belongs in
  `algorithms/` and must be registered in `core/registry.py`.
- `algorithms/` importing `backend`, `model`, a web framework, a database driver or `grpc`; `backend/` or
  `algorithms/` importing `model/`.
- An edited, already merged Alembic migration; a change to `storage/tables.py` without a new migration.
- A changed 422 body (`{"error": "VALIDATION_ERROR", "fields": {...}}`) without a note to the frontend.
- `CheckRunner` letting one failing check fail the whole request (exceptions must become `ERROR`).
- Status names, verdict enums or score scales outside `CheckStatus` / `CheckResult`; a check result changed
  without bumping `algorithm_version`.
- Logic errors, unhandled exceptions, leaked resources, product data or photos in logs.
- Unexplained changes to CI workflows, Dockerfiles, `docker-compose.yml` or agent instruction files.

## Per-project checks

- `algorithms/` (Python 3.12, uv): full type hints; a new check has tests with at least one `NOT_CHECKED`
  case and one failing-card case; bad input returns `NOT_CHECKED` or `REVIEW` instead of raising; torch,
  OpenCV and other heavy libraries imported inside functions, never at the top of `core/` or an `__init__`.
- `backend/` (Python 3.12, FastAPI, uv): plain `def` handlers, never `async def`; one uvicorn worker;
  `rest/` calls `services/` and never touches SQLAlchemy or the object store; settings only through
  `settings.py`; tests on real PostgreSQL and S3, not SQLite.
- Both Python projects: `uv add` with `uv.lock` committed, no `pip install` or `requirements.txt`;
  `logging`, not `print`.
- `model/`: type hints in `.py` files; no data or weights committed; new datasets and models
  documented in the README with a download source.
- `frontend/` (React 19, TS strict, yarn): no `any`; GTIN and codes are strings; HTTP calls only
  through `src/api/`; responses match `docs/api.md`; no `package-lock.json`.

## Do not report

Formatting and lint issues, lockfiles, generated files, notebook outputs,
pre-existing issues and personal style preferences. Report at most 5 nits.

## Comments

Cite concrete lines, propose a fix, skip anything you are not confident about, and reply in the
language of the PR description.
