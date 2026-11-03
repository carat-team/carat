# REVIEW.md

Rules for reviewing a pull request in the Carat repository. Used by human reviewers and by AI reviewers
(`claude-code-review.yml`). Read the root `AGENTS.md` and the `AGENTS.md` of every touched project first.

## How to review

1. Read the PR title, description and (if possible) linked Taiga task. Understand what the change is supposed to do.
2. Read the diff against the rules below. Group findings by severity.
3. Reply in the language of the PR description (Russian or English).

## Blocking (must be fixed before merge)

### Invalid placement and architecture consistency

- Check logic in `backend/` (rules, parsers, text comparison, image analysis, model calls).
  It belongs in `algorithms/` and must be registered in `core/registry.py`.
- `algorithms/` imports `backend`, `model`, a web framework, a database driver or `grpc`.
- `backend/` or `algorithms/` imports from `model/`.
- New top-level project, server, Dockerfile or service that was not agreed.
- `rest/` reaches into `storage/` or SQLAlchemy sessions directly, skipping `services/`.

### Python backend rules

- `CheckRunner` changed so that a failing check can fail the whole request (exceptions must become `ERROR`).
- Bare `except:` or `except Exception: pass`. Swallowed errors without a reason code or a log line.
- Edited an already merged Alembic migration instead of adding a new one.
- Changed 422 response shape (`{"error": "VALIDATION_ERROR", "fields": {...}}`) without a note to the frontend.

### Results and vocabulary

- New status names, verdict enums or score scales outside `CheckStatus` / `CheckResult`.
- A check result without `reason_code`, `explanation` or `algorithm_version`.
- A check changed in a way that can alter results, but `algorithm_version` is not bumped.
- A check that raises on bad or missing input instead of returning `NOT_CHECKED` or `REVIEW`.
- Card contents, field values or photos written to logs.

### Dependencies and files

- `uv.lock` changed without `pyproject.toml`, or the reverse. CI runs `uv lock --check` for each project.
- `pip install`, `requirements.txt`, hand-made venv.
- Heavy library (OpenCV, onnxruntime, torch) imported at the top of `core/` or a package `__init__`.
- Committed secrets, `.env`, model weights (`*.pth`, `*.safetensors`, `*.onnx`), datasets, CSV dumps,
  archives, build output, photos over 100 KB.
- A test that depends on a file outside the repository.

### Tests

- A deleted or weakened test with no explanation in the PR.
- A new check without tests, or without at least one `NOT_CHECKED` case and one failing-card case.
- `backend` tests that re-test check logic instead of runner and API behaviour.

### Process

- PR not targeting `dev`, or commits made directly to `dev` / `master`.
- Version changed in only some of `backend/pyproject.toml`, `algorithms/pyproject.toml`, `frontend/package.json`.
- Edits to `AGENTS.md`, `CLAUDE.md`, CI, release workflows, Dockerfiles or compose without a reason in the PR.

## Frontend

- `any` in TypeScript without a comment, unused exports, API calls outside `src/api/`.
- `yarn ts:check`, `yarn lint:fix` and `yarn format` must pass (the pre-commit hook runs them).
- Response handling must match the backend contract in `docs/api.md`.

## Non-blocking

- Naming that is unclear, single-letter variables outside loop counters.
- Missing type hint on a private helper, `print` in a script.
- Comment that restates the code.
- Single-character arrows or em/en dashes in code, comments or docs (write `->` and `-`).
- Large PR that could have been split.

## Do not report

- Style that `ruff` or `prettier` already enforces and CI already checks.
- Personal preference with no rule behind it.
- Issues in code the PR did not touch.
- Anything in `.context/`, which is agent scratch space.
- Missing features that the Taiga task does not ask for.

## PR title and description

- Title: English, imperative, capitalized, no period, up to 50 characters. It becomes the commit message.
- Description: what changed, why, how to test, Taiga link. Written in Russian or English.
- One PR = one task.
