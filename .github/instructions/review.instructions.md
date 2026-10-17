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
- An edited existing Flyway migration; a schema change without a new migration.
- A `proto/` change without matching backend and inference updates.
- `io.github.duckysmacky.cogniflex` importing `io.github.carat_team.carat`; `inference/` importing `model/`.
- Logic errors, unhandled exceptions, leaked resources, product data in logs.
- Unexplained changes to CI workflows, Dockerfiles, `docker-compose.yml` or agent instruction files.

## Per-service checks

- `backend/` (Java 25, Spring Boot 4): records for DTOs and config, switch expressions and pattern
  matching, constructor injection, no field `@Autowired`, no Lombok, no `Optional` fields,
  explicit imports. New rules, services and endpoints need tests (`@WebMvcTest` + `@MockitoBean`).
- `inference/` (Python 3.12, uv): full type hints on every function; models loaded once at
  startup; gRPC errors via `context.set_code`; `logging`, not `print`; deps via `uv add` with `uv.lock`.
- `model/`: type hints in `.py` files; no data or weights committed; new datasets and models
  documented in the README with a download source.
- `frontend/` (React 19, TS strict, yarn): no `any`; GTIN and codes are strings; HTTP calls only
  through `src/api/`; no `package-lock.json`.

## Do not report

Formatting and lint issues, lockfiles, the Gradle wrapper, generated stubs, notebook outputs,
pre-existing issues and personal style preferences. Report at most 5 nits.

## Comments

Cite concrete lines, propose a fix, skip anything you are not confident about, and reply in the
language of the PR description.
