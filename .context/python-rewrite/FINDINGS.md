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
