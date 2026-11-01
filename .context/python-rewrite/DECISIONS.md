# Decisions

## 2026-10-31 - Legacy tag on dev head

**Status:** accepted

**Decision:** Tag `legacy/java-backend` points at `fe69e60` (dev head before any rewrite commit) and is pushed to origin.

**Rationale:** Last state of the shared branch with all Java and Cogniflex code; reachable from `dev` history.

**Impact:** Step 1 of the plan.

## 2026-10-31 - Torch approved for OCR in the [ml] extra

**Status:** accepted

**Decision:** Keep EasyOCR (ru + en, `min_confidence` 0.3, `max_image_side` 1600). Torch from the CPU index goes
into the `[ml]` extra of `algorithms`, never into core.

**Rationale:** Straight port of merged PR #21; model switch (RapidOCR/ONNX) would be new work.

**Impact:** Image size and RAM grow; memory budget still to be measured (open question in the plan).

## 2026-10-31 - Ported label checks report validity only

**Status:** accepted

**Decision:** Port as `gtin_format` (validates `card.gtin`) and `barcode_on_photo` (decodes photos, validates each
code). OCR becomes an unregistered reader helper for future checks. No comparison of decoded GTIN with the card.

**Rationale:** The old code returned raw scan data, not a verdict. The plan forbids new check logic during the rewrite.

**Impact:** Step 7 scope. GTIN comparison is a follow-up.

## 2026-10-31 - Rewrite context tracked in the repository

**Status:** accepted

**Decision:** Context lives in `.context/python-rewrite/` (committed), not in gitignored `.context/local/`.
Plan, port table and progress moved into `notes/`.

**Rationale:** User choice: others can see progress on the branch.

**Impact:** ADR links updated. Context edits are committed once at the start and once at the end, not per step.

## 2026-10-31 - No throwaway check in the algorithms scaffold

**Status:** accepted

**Decision:** Step 4 tests the core models and registry only; the first real check is the GTIN port in step 7.

**Rationale:** A placeholder check would be deleted a few commits later.

**Impact:** Deviation from plan step 4 ("one trivial check").

## 2026-10-31 - algorithm_version is an integer

**Status:** accepted

**Decision:** `CheckResult.algorithm_version` and `Check.algorithm_version` are `int`, starting at 1 and bumped by 1
on any change that can alter a result.

**Rationale:** User request. A counter is easier to compare and bump than a semver string.

**Impact:** `docs/api.md` example changed to `"algorithm_version": 1`; frontend types in step 9 use `number`.

## 2026-10-31 - README for humans, AGENTS.md for agents

**Status:** accepted

**Decision:** `algorithms/README.md` and `backend/README.md` hold the human explanation (setup, recipes, check
example, status meaning, design rationale). Both `AGENTS.md` files keep short, concrete rules and point to README.

**Rationale:** User request; AGENTS.md was mixing rationale with instructions.

**Impact:** `backend/AGENTS.md` (already committed in `ca50697`) changes in the "Scaffold backend service" commit.
README sections that describe current state (endpoints, settings, weights) must be updated in steps 7, 8 and 10.

## 2026-10-31 - One commit per ported check

**Status:** accepted

**Decision:** User reviews and commits each step-7 port separately (`ce9a670` GTIN), instead of one step-7 commit.

**Rationale:** User request after reviewing the GTIN port.

**Impact:** Barcode and OCR get their own commits after review.

## 2026-10-31 - Backend depends on carat-algorithms[vision]

**Status:** proposed (awaiting user review)

**Decision:** `backend/pyproject.toml` requires `carat-algorithms[vision]`, because the registered
`barcode_on_photo` check imports zxing-cpp and Pillow at run time.

**Rationale:** Without the extra the check raises `ImportError` and the runner reports `ERROR` on every card.

**Impact:** Backend image grows by Pillow + zxing-cpp (small). `[ml]` stays out until a registered check needs it.

## 2026-10-31 - Backend installs every algorithms extra

**Status:** accepted (supersedes "Backend depends on carat-algorithms[vision]")

**Decision:** `backend` depends on `carat-algorithms[vision,ml]`.

**Rationale:** User request: avoid dependency surprises when new checks start using an extra.

**Impact:** Backend environment and image include CPU torch and EasyOCR. A new extra must be added to this list.

## 2026-10-31 - No "inferred" marker, no guillemets

**Status:** accepted

**Decision:** Check docstrings do not carry an "inferred" line (rule removed from `algorithms/AGENTS.md` and README).
Code, comments and explanations use plain quotes, never `«»` (new Style rule in `algorithms/AGENTS.md`).
Port commits cite the source PR in their body.

**Rationale:** User request.

**Impact:** Root `AGENTS.md` ("must be marked as such") and `docs/requirements.md` still mention the "inferred"
marker; left unchanged pending the user's call. `d9f9afc` amended the GTIN commit for these changes.

## 2026-10-31 - Step 8 API and storage choices

**Status:** accepted

**Decision:** POST `/api/products` requires `fullName`, `gtin`, `tnVedCode`; PATCH cannot null them. Check
results are returned, not stored. PostgreSQL stays; schema and migrations start from zero. Photos in root
`data/photos/`, weights in root `weights/<model family>/`, both gitignored with `.gitkeep`. DB tests skip
without `TEST_DATABASE_URL`; `just backend test-db` starts postgres:18 on port 55432. Compose stays untouched
until step 10.

**Rationale:** User answers; the test-DB default was taken because that question got no direct answer.

**Impact:** `docs/api.md` does not yet describe the product response (`id`, `createdAt`, `photos`), required
fields or 404s; left for the user to decide.

## 2026-10-31 - Step 8 reworked to the CARAT_MVP spec

**Status:** accepted (supersedes "Step 8 API and storage choices")

**Decision:** API, storage and data follow `CARAT_MVP.xlsx`: `{attributes}` bodies, EAV `product_attributes`,
status column, list = MVP fields + gtin/brand/createdAt/photoUrl. Partial drafts, format-only validation,
`tnVedCode` defaults to 3303. Photos in S3-compatible storage (ADR 0002), RustFS because MinIO images are gone.
Layout `domain/`, `services/` (runner merged into `checks.py`), `storage/`, `rest/{routers,schemas}`, one
`bootstrap.build_services()` for REST and a future gRPC adapter (no gRPC code yet). Non-secret settings in
`backend/settings.toml` (`SETTINGS_FILE` override), DB as `DB_*` and storage keys as `S3_*` in `.env`.
`weights/<model>/.gitkeep`, `[weights] easyocr_dir`. Root `data/` dropped. No `# ponytail:` comments.

**Rationale:** User answers and review comments on the first step-8 version.

**Impact:** docs/api.md rewritten in Russian from the MVP; compose still describes the old stack until step 10.

## 2026-11-01 - Skip step 9 (frontend wiring)

**Decision:** Leave `frontend/` unchanged; no API client, type or Docker changes for it in this PR.
**Rationale:** User: wiring the UI now would take the frontend team's work; they have `docs/api.md` and the MVP.
**Impact:** Step 12 end-to-end runs through the API (curl), not the UI. No frontend service in compose.

## 2026-11-01 - Compose layout for the backend

**Decision:** Services `db`, `s3` (RustFS), one-shot `migrate` (`alembic upgrade head`, same image) and `backend`.
Containers get `DB_*`/`S3_*` through an `x-backend-env` anchor interpolated from `.env`, plus `DB_HOST=db` and
`SETTINGS_FILE` pointing at the mounted `backend/settings.docker.toml`.
**Rationale:** Migrations run once before the API starts; explicit env instead of `env_file` keeps unrelated `.env`
vars out of the containers and works with `--env-file`.
**Impact:** CI runs plain uv commands (no `just` action); setup-uv pinned to v10.3.3 (no floating major tag).

## 2026-11-01 - Object storage connection in env

**Decision:** `S3_ENDPOINT`, `S3_BUCKET`, `S3_SECURE` join `S3_ACCESS_KEY`/`S3_SECRET_KEY` in env; one
`ObjectStorageSettings(BaseSettings, env_prefix="S3_")`; no `[object_storage]` TOML section.
**Rationale:** User: connection settings belong with the other `.env` connection data, like `DB_*`.
**Impact:** compose sets `S3_ENDPOINT=s3:9000`; `settings.docker.toml` only differs in the weights path.

## 2026-11-01 - One settings file, WEIGHTS_DIR by convention

**Decision:** `settings.docker.toml` removed; compose mounts `backend/settings.toml` over the image copy (edit +
restart to tweak). `[weights] easyocr_dir` replaced by env `WEIGHTS_DIR` (root dir, relative resolves against the
TOML's directory, image sets `/app/weights`); each model picks its subdirectory (`OcrReader(weights_dir)` uses
`WEIGHTS_SUBDIRECTORY = "easyocr"`).
**Rationale:** User: local/docker split and per-model weight paths were clunky; still wants a mounted settings file.
**Impact:** New model family needs only `weights/<family>/.gitkeep`, no setting.

## 2026-11-01 - Writing style rule

**Decision:** Root `AGENTS.md` "Writing style": no single-character arrows (write `->`), no em/en dashes (write
`-`), no `«»` in code and comments (moved from `algorithms/AGENTS.md`). `REVIEW.md` lists it as non-blocking.
**Rationale:** User request. Left as-is: `frontend/src/components/ui/Select/Select.tsx` comments (frontend code
untouched by request) and the sample texts in `model/*.py` (data strings).
**Impact:** The `## graphify` section of the root AGENTS.md was folded into "Tools and skills".
