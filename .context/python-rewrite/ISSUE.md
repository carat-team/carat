---
id: python-rewrite
status: open
kind: refactor
created: 2026-10-31
updated: 2026-10-31
---

# Rewrite Carat from Java + Cogniflex to Python

## Summary

Replace the Java backend, the Python inference service and the gRPC contract with two uv projects:
`algorithms/` (`carat_algorithms`, pure checks) and `backend/` (`carat_backend`, FastAPI + PostgreSQL 18).
Decision record: [ADR 0001](../adr/0001-rewrite-in-python.md).

## Scope

In scope: port logic already merged into `dev` (GTIN/barcode validator and reader, label OCR, frontend API
client, tooling) into the new layout, following the 12 steps in [rewrite-plan.md](notes/rewrite-plan.md).

Out of scope: open PRs #12, #16, #17, #19 and every new check (R2, R4, R6, R7, R8). They land after the
rewrite, see [port-table.md](notes/port-table.md). No AI-content detection.

Progress per step: [rewrite-progress.md](notes/rewrite-progress.md).

## Acceptance criteria

- [ ] Tag `legacy/java-backend` exists on origin
- [ ] Java backend, `inference/`, `proto/` and Java CI removed
- [ ] `algorithms/` and `backend/` pass `just check`
- [ ] Every Java BarcodeValidator / BarcodeReader test case ported and passing
- [ ] Endpoints from `docs/api.md` implemented, 422 shape unchanged
- [ ] `docker compose up --build` runs db + s3 + backend; one card checked end to end through the API (frontend untouched, step 9 skipped)
- [ ] CI runs both Python projects with `uv lock --check`
- [ ] Draft PR into `dev` marked ready after user approval

## Links

- Branch: `refactor/python-rewrite`, Draft PR #26 into `dev` (mark ready only after step 12)
- Root rules: `AGENTS.md`, `REVIEW.md`, `algorithms/AGENTS.md`, `backend/AGENTS.md`
- Requirements: `docs/requirements.md`, API contract: `docs/api.md`
