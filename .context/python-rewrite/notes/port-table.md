# Port table: what to carry into the new layout

Agent-facing. Source: PR list and file lists on `dev` as of 2026-10-28. The "Verified" column is empty on purpose:
fill it in step 2 of `.context/python-rewrite/notes/rewrite-plan.md` by reading the code at tag `legacy/java-backend`.
Open PRs are **out of scope of the rewrite**: they land after it (see below).

## Merged into `dev` and worth keeping

| PR | What | Old location | New home | Action | Verified |
|---|---|---|---|---|---|
| #21 | GS1 checksum and length validation (EAN-13/8, UPC-A/E, ITF-14), DataMatrix `01<GTIN>21<serial>` structure | `backend/src/main/java/.../services/barcode/BarcodeValidator.java` + `BarcodeValidatorTest.java` | `algorithms/identifiers/gtin/` | Rewrite rules in Python, port every test case | 2026-10-31: 19 cases in port-fixtures.md |
| #21 | Barcode decoding | `.../barcode/BarcodeReader.java` (ZXing, Java ImageIO) | `algorithms/vision/barcode/` | Reimplement with `zxing-cpp`; fixes the WebP limitation | 2026-10-31: TRY_HARDER multi-decode, 3 cases |
| #21 | OCR of labels (ru + en, EasyOCR, resize to `max_image_side`) | `inference/app/detectors/ocr_detector.py` | `algorithms/vision/ocr/` | Keep model choice and resize rule; lazy load behind a lock; weights not in git | 2026-10-31: ru+en, 0.3, 1600; no unit tests at tag |
| #21 | Label scan orchestration | `LabelScanService.java`, `LabelController.java`, DTOs | `backend/services/` + one `CheckResult` per check | Do not port the DTO shapes; results use `CheckResult` | 2026-10-31: only empty/undecodable upload errors worth keeping |
| #21 | OCR proto and gRPC client | `proto/carat/inference/ocr.proto`, `OcrGrpcClient.java` | - | Delete (no inference service) | 2026-10-31 |
| #10 | SigLIP 2 frame/perfume classifier experiments and reports | `model/training/frame_classifier/` | `model/` (stays) | Keep as research. Weights live on branch `chore/add-frame-classifier-weights`; `predict.py` is the starting point for a future vision check | 2026-10-31: stays in `model/`, untouched |
| #9, #14, #15, #18, #22, #23, #24 | Frontend types, routes, API client, header, product code step, husky | `frontend/` | `frontend/` (stays) | Keep; re-point API client to the new endpoints | 2026-10-31: API client is a demo stub (`/example/path`), replace in step 9 |
| #11 | Agent tooling: skills, graphify, worktree conventions | `.agents/`, `AGENTS.md`, `REVIEW.md` | same | Keep skills; `AGENTS.md` and `REVIEW.md` replaced by the new versions | 2026-10-31: replaced in `9f6d8da` |
| #6, #7 | uv project pattern, justfile, uv base Docker image, CPU torch index | `inference/` | pattern only | Reuse the pattern for both new projects. No torch in `algorithms` core | 2026-10-31: uv python3.12-bookworm-slim image, pytorch-cpu explicit index |
| #3, #4, #2 | Version tags, release workflow (push to master -> `:latest`, tag -> `:<version>`), extension removed | `.github/workflows/release.yml` | same | Keep logic, switch to the two new images | 2026-10-31: matrix `[backend, inference]`, repo-root context; becomes `[backend]` only (algorithms is a library, no image) |

## Open PRs: out of scope, land after the rewrite

Do not port these during the rewrite. Their authors rebase onto the new layout (or we port them) once the rewrite is merged.
The table only records where each one will go.

| PR | Author | What | New home | Action after rewrite | Verified |
|---|---|---|---|---|---|
| #16 | Nnnikitosss | Volume consistency check: `parsing.py`, `checker.py`, `config.py`, `test_volume_check.py` (270 lines of tests) | `algorithms/text/volume/` (R5) | Port rules and tests; map its verdicts to `CheckStatus` | |
| #19 | Liks-Lee | Perfumery name/type check: `perfumery_name_check.py`, `evaluation.py`, `check_catalog.py`, tests | `algorithms/text/perfumery_type/` (R3) | Port rules and tests; move evaluation code to `algorithms/scripts/`; `test_metrics_and_quality.py` needs `gold_labeled.csv` which is not committed: get a small fixture or drop | |
| #12 | newplays | Image quality: `inference/app/quality/image_quality.py` + tests | `algorithms/vision/quality/` | Port the OpenCV logic and thresholds; drop gRPC and Java client | |
| #17 | yaurnee52 | Background and foreign objects check, implemented in Java | `algorithms/vision/background/` | Take thresholds and test cases only; reimplement with `opencv-python-headless` (and `rembg` only if approved) | |

## Not ported

- Everything AI-content related: detectors, `AnalyzerGrpc`, static-analysis config (`static-analysis-config.yml`),
  `docs/ai-*`, `docs/gRPC.md`.
- Java build files, Flyway migrations, Spring configuration, proto files, `inference/` Dockerfile and compose service.
- Redis service in `docker-compose.yml`.

## New checks with no existing code (also after the rewrite)

The rewrite only ports existing Carat logic. These are planned follow-ups, not part of it.

| Requirement | Check | Notes |
|---|---|---|
| R2 (79.1% of real errors) | Brand attribute vs brand in name | Highest value, no code anywhere; start here after GTIN and volume |
| R4 | Brand value `Без товарного знака` invalid | Trivial rule; normalise case and quotes |
| R6 | One-word / type-only names | Needs the list of perfumery type words from the R3 check |
| R7 | TN VED code vs perfumery type | Needs a mapping table from ЧЗ |
| R8 | Field IDs and limits per ППР № 1957 | Source: Attributes Model.xlsx |
