# Rewrite plan: Java + Cogniflex -> Python (`algorithms` + `backend`)

Agent-facing. Read with `.context/adr/0001-rewrite-in-python.md` and `.context/python-rewrite/notes/port-table.md`.
Update `.context/python-rewrite/notes/rewrite-progress.md` after every step so the next session can resume.

## Scope

- **In scope:** port the logic that already exists on `dev` (GTIN/barcode validator and reader, OCR, frontend, tooling)
  into the new Python layout.
- **Out of scope:** the currently open PRs (#12, #16, #17, #19) and every new check (R2, R4, R6, R7, R8).
  They land after the rewrite is merged, on top of the new layout. See `.context/python-rewrite/notes/port-table.md`.

## Rules for this work

- One long-lived Draft PR into `dev` from `refactor/python-rewrite`, commits grouped **per feature**: one commit per
  coherent piece (for example "Remove the Java backend", "Scaffold algorithms library", "Port GTIN validator").
  Not one giant commit, not a commit per file. Merge method at the end: "Rebase and merge" (a maintainer enables it
  temporarily; the repo is squash-only).
- **Manual review after every step.** Finish a step, update `rewrite-progress.md`, report what changed, then stop and
  wait for the user's go-ahead before starting the next step. Applies until the user says otherwise.
- Do not rebase onto new work from others unless asked.
- Commit titles follow the root `AGENTS.md` style (`Add X`, `Remove Y`, `Port Z`). Stage files by name, no `git add .`.
  Commit only when the step is reviewed or the user asks.
- Destructive steps (tag, deleting directories) need explicit user confirmation first.
- Run `just check` before every commit that touches a Python project.
- Do not port AI-content detection. Do not add checks that are not already implemented on `dev`.

## Current repo state (2026-10-31)

- `backend/` still holds the old Java backend (Gradle, `src/`, `Dockerfile`, `AGENTS.md`).
- `new-backend/` (untracked) is a temporary directory with the new backend's `AGENTS.md` and `justfile`.
- `algorithms/` (tracked) holds only `AGENTS.md` and `justfile`. Root `justfile` (untracked) has `mod backend` and `mod algorithms`.
- Not yet deleted: `inference/`, `proto/`. Tag `legacy/java-backend` does not exist yet.

## Steps (in order, each is one or a few commits)

1. **Preserve.** Tag the last pre-rewrite commit `legacy/java-backend` and push the tag. Confirm with the user first.
2. **Inventory.** Fill the "Verified" column for the merged-into-`dev` rows of `.context/python-rewrite/notes/port-table.md` by reading
   the code at the tag. Copy test cases and fixtures you intend to port into a scratch note in `.context/python-rewrite/notes/`.
3. **Delete and rename.** Remove the old Java `backend/`, `inference/`, `proto/`, Java-specific CI (`backend-tests.yml`)
   and Cogniflex docs (`docs/gRPC.md`, `docs/ai-*`). Then `git mv`-style rename `new-backend/` -> `backend/`
   (it is untracked, so a plain `mv` after the deletion). Keep `frontend/`, `model/`, relevant `docs/`, `.agents/`.
   Commits: "Remove the Java backend and inference service" and "Add new backend project instructions"
   (plus root/algorithms `justfile`s and `AGENTS.md` if they fit better with step 6).
4. **Scaffold `algorithms/`.** `uv init --lib`, `src/carat_algorithms/core/` with `ProductCard`, `CheckStatus`,
   `CheckResult`, `Check` protocol, registry. Ruff/pyright/pytest config (the `justfile` and `AGENTS.md` already exist),
   one trivial check with tests.
5. **Scaffold `backend/`.** FastAPI app factory, settings, `/health`, path dependency on `../algorithms`
   (`editable = true`), `CheckRunner` with a fake-check test proving `ERROR` isolation. `AGENTS.md` and `justfile`
   (`run` uses `--workers 1`) already exist after step 3.
6. **Root files.** Root `justfile` (already drafted), `.gitignore`, `.env.example`, `CODEOWNERS`.
   No root `pyproject.toml`.
7. **Port existing checks, one commit per check**, in this order: GTIN/barcode validator and reader, OCR.
   Each port: copy rules and test cases from the tag, rewrite in the `Check` shape, add `NOT_CHECKED` cases, register.
   Nothing from open PRs, no new checks.
8. **Backend features.** Postgres models and Alembic initial migration, products and photos endpoints per `docs/api.md`,
   `POST /api/products/{id}/check`, photo storage.
9. **Frontend wiring.** Point the existing API client at the new endpoints; keep the 422 shape.
10. **Docker and CI.** Dockerfiles with the repo root as build context, `--no-editable`, `uv lock --check` per project,
    compose with `db` (postgres:18) and `backend`. Update `release.yml`, add `algorithms-tests.yml`, `backend-tests.yml` (Python).
11. **Docs.** README, per-project READMEs (weights table), `docs/how-to-add-a-check.md` (Russian, human-facing).
12. **Final check.** `just check` at the root, `docker compose up --build`, one end-to-end card through the frontend.
    Then mark the PR ready.

## Open questions (do not decide silently)

- Memory budget for OCR (and later SigLIP, rembg) in one process: measure first, then decide which vision checks ship.
- Source of the TN VED -> perfumery type table for R7.
- Result format ЧЗ will actually consume; keep the single vocabulary until told otherwise.
- After the rewrite: `gold_labeled.csv` is referenced by the PR #19 tests but not committed; ask the author for a fixture or drop those tests.
