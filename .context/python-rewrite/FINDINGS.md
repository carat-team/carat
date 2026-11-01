# Findings

## 2026-10-31 - Repository state at the start of the rewrite

Branch `refactor/python-rewrite` is one commit ahead of `dev` (`9f6d8da` on top of `fe69e60`). That commit already
deleted `docs/gRPC.md` and `docs/ai-*`, so plan step 3 does not need to touch them. `algorithms/` (AGENTS.md,
justfile), `new-backend/` and the root `justfile` were untracked. No git tags existed.

**Evidence:** `git log`, `git status`, `git tag` on 2026-10-31.

## 2026-10-31 - Frontend API client is a demo stub

`frontend/src/api/analyze/` only holds an example request to `/example/path`; there are no real endpoints to
re-point. Step 9 replaces it with a products client.

**Evidence:** `frontend/src/api/analyze/analyze.api.ts`, `types.ts` (TODO "demonstration example").

## 2026-10-31 - Port sources are small

BarcodeValidator 100 lines, BarcodeReader 39, OcrDetector 26, plus 2 Java test classes (10 test methods).
Details and every test case: [port-fixtures.md](notes/port-fixtures.md).

**Evidence:** `wc -l` at `fe69e60`.

## 2026-10-31 - Leftovers that still reference the removed services

After step 3, `release.yml` still calls the deleted `backend-tests.yml` and builds an `inference` image,
`docker-compose.yml` still defines the `inference` and Redis services, `.dockerignore` and `.gitignore` list
`inference/` paths, `README.md` describes the old layout, and `.github/instructions/review.instructions.md`
(Copilot review rules) talks about `proto/`, `inference/` and Java packages. Release CI is broken on this branch
until step 10. Fix in steps 6 (ignore files), 10 (CI, compose, review instructions) and 11 (README).

**Evidence:** `grep -rn 'inference|proto/|backend-tests'` after commit `15b0452`.

## 2026-10-31 - Starlette 1.x TestClient needs httpx2

Starlette 1.10 imports `httpx2` for `TestClient` and only falls back to `httpx` with a deprecation warning; with
plain `httpx` pyright strict reports the client as unknown. Backend dev group uses `httpx2`.

**Evidence:** `backend/.venv/.../starlette/testclient.py` lines 26-41; `just backend check` green after the swap.

## 2026-10-31 - ruff formats Python blocks inside Markdown

ruff 0.17 reformatted the code block in `algorithms/AGENTS.md` during `ruff format .`. Both projects set
`extend-exclude = ["*.md"]`; the AGENTS.md change was reverted.

**Evidence:** diff on `algorithms/AGENTS.md` after `just algorithms fix`.

## 2026-10-31 - Registry must import checks lazily

`core/__init__.py` re-exports `get_checks`, and check modules import `carat_algorithms.core`, so a top-level import
in `registry.py` is circular. `get_checks()` imports the check classes inside the function; this also keeps
`import carat_algorithms.core` free of `identifiers` and vision modules.

**Evidence:** `import carat_algorithms.core` leaves no `carat_algorithms.identifiers` in `sys.modules`.

## 2026-10-31 - zxing-cpp 3.1 differs from ZXing Java on UPC-E and text modes

- Default `TextMode.HRI` renders the GS separator as `<GS>` and GS1 payloads as `(01)...`; `TextMode.Plain`
  returns `0104600439931256215Q8H6t\x1d93abcd` for both plain and GS1 (`]d2`) DataMatrix, same as ZXing Java.
- UPC-E is reported expanded to 13 digits (`0042100005264`); the original 8 digits are in `barcode.extra["UPCE"]`.
  The reader uses them so the ported UPC-E rule stays intact.
- `write_barcode_to_image` returns a `zxingcpp.Image` with `shape` and the buffer protocol; no numpy needed.
  GS1 DataMatrix test codes: `create_barcode("(01)...(21)...", DataMatrix, gs1=True)`.

**Evidence:** probe scripts against zxing-cpp 3.1.1; `tests/vision/barcode/test_reader.py`.

## 2026-10-31 - uv sources of a path dependency do not apply to the dependent project

`algorithms` pins torch to the explicit `pytorch-cpu` index, but `backend` locks `carat-algorithms` as a path
dependency, and uv ignores that project's `[tool.uv.sources]`. `backend/pyproject.toml` repeats the torch and
torchvision sources and the index; with it, neither lock contains an `nvidia` package.

**Evidence:** `grep -c nvidia backend/uv.lock algorithms/uv.lock` -> 0; torch source `download.pytorch.org/whl/cpu`.

## 2026-10-31 - EasyOCR ru + en needs two weight files

`craft_mlt_25k.pth` (md5 `2f8227d2...`) and `cyrillic_g2.pth` (md5 `19f85f43...`); `english_g2.pth` is not loaded.
`OcrReader` with `download_enabled=False` reads them from `weights_directory` and recognised text on a test image.

**Evidence:** real download into the session scratchpad, md5sum matches `easyocr/config.py`, smoke run output.

## 2026-10-31 - App logs are not configured yet

Under `just backend run` only uvicorn's own logs appear; `CheckRunner` info lines are dropped because nothing
configures the `carat_backend` loggers. No card contents appear in the server log.

**Evidence:** smoke run log in the session scratchpad (create, upload EAN-13 PNG, check: both checks PASS).

## 2026-10-31 - MinIO community images are no longer pullable

`docker pull minio/minio` (Docker Hub) and `quay.io/minio/minio` both refuse access. `rustfs/rustfs:1.0.4`,
`chrislusf/seaweedfs` and `dxflrs/garage` are available; RustFS works with the `minio` Python client
(bucket create, put, get with content type, delete).

**Evidence:** docker run / manifest inspect output; probe script against `carat-test-s3`.

## 2026-11-01 - Backend image facts

The venv must keep the same absolute path in builder and runtime: console scripts (`alembic`, `uvicorn`) have the
builder's venv path in their shebang. `UV_PROJECT_ENVIRONMENT=/app/.venv` fixes it. `python:3.12-slim-trixie` needs
no extra apt packages for easyocr/opencv-headless/zxing-cpp/torch. Image size 1.59 GB. RustFS 1.0.4 stores data in
`/data` (`RUSTFS_VOLUMES=/data`), runs as user `rustfs`, ports 9000 (S3) and 9001 (console).
**Evidence:** `docker compose up` run on 2026-11-01: migrate exit 0, `/health` ok, both checks PASS on an EAN-13 photo.
