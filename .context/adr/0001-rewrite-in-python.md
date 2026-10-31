# ADR 0001. Rewrite the project in Python and extract the algorithms library

Status: accepted (live-sync, October 2026)
Date: 2026-10-28

## Context

Carat started as a fork of Cogniflex (an AI-content detector). The customer (Честный Знак) needs checks of product cards in the category «Парфюмерия» (perfumery). Cogniflex's architecture (Spring Boot -> gRPC -> Python inference) does not fit this task:

- The rule "backend is always Java" left no room for Python algorithms, so the checks were written again in Java (for example, OpenCV logic in PR #17).
- The vast majority of participants know only Python.
- Two language environments and the gRPC contract between them slow down every new check.
- Most of the Cogniflex code (AI-content detectors, static and dynamic analysis) is not needed by the customer.

## Decision

1. Remove the Cogniflex code: the inference service, its gRPC contract, static and dynamic analysis, and all the Java.
2. Create two independent uv projects, each with its own `pyproject.toml` and `uv.lock` (the root has no manifest):
   - `algorithms/` (`carat_algorithms`) - a library of checks without transport and without a DB;
   - `backend/` (`carat_backend`) - FastAPI, PostgreSQL, running checks; imports `algorithms`.
3. The backend serves REST for the frontend. A gRPC interface for ЧЗ services will be added later as a second adapter over the same `services/` layer.
4. One result vocabulary for all checks: `PASS`, `WARNING`, `REVIEW`, `NOT_CHECKED`, `ERROR`.
5. The database is PostgreSQL 18; Redis is not needed. Card attributes are stored in JSONB.
6. One uvicorn process (`--workers 1`), only `def` handlers, heavy checks behind a semaphore.
7. Valuable code already merged into `dev` is moved to the new structure; PRs still open at the time of the rewrite are out of scope and land after it, rebased onto the new layout (see `.context/python-rewrite/notes/port-table.md`). The old state is preserved under the `legacy/java-backend` tag.

## Consequences

Pros:
- The ML team adds a check in one place without touching the backend.
- One language for all server code and all newcomers.
- Checks are tested without running a server or database.

Cons and risks:
- Rewrite in one long-lived PR; open PRs #12, #16, #17, #19 are not part of it, so their authors must rebase onto the new layout once the rewrite is merged (their logic is listed in `.context/python-rewrite/notes/port-table.md`).
- Heavy models (SigLIP, EasyOCR, rembg) in one process may not fit in memory; measure before promising the set of checks.
- The Taiga wiki will go stale; it is updated separately.

## Alternatives considered

- Keep the Java backend and add `algorithms` as a service: keeps the gRPC boundary and two environments, does not solve the onboarding problem.
- A monorepo with a uv workspace and a shared `pyproject.toml` at the root: rejected, the root must stay clean.
- Async FastAPI handlers: rejected, the checks are blocking and CPU-bound.
