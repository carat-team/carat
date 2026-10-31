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
