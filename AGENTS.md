# AGENTS.md

Instructions for AI agents working in the Carat repository. `CLAUDE.md` is a symlink to this file.
Each project has its own `AGENTS.md` with stack, build and style rules - read it before touching that directory.

## What Carat is

Carat checks product cards for the "Честный Знак" (ЧЗ) marking system, perfumery category only.
A card is structured attributes (name, brand, perfumery type, volume, TN VED code, GTIN, ...) plus photos.
Carat runs a set of independent checks and returns one result per check: `PASS`, `WARNING`, `REVIEW`,
`NOT_CHECKED` or `ERROR`, each with a reason code and a human-readable explanation. Carat does not
accept or reject cards by itself; the consumer (our frontend, later ЧЗ services) applies its own policy.

`docs/requirements.md` lists the customer requirements (R1-R8) and is the source of truth for which
checks exist. Checks not on that list are allowed but lower priority.

Carat started as a fork of Cogniflex, an AI-generated content detector. That code is gone and is kept
under the git tag `legacy/java-backend`. Do not port AI-content detection (human/ai verdicts, static
text signals, RoBERTa/ResNet detectors) back into this repository.

## Repository map

| Path | What | Stack |
|---|---|---|
| `algorithms/` | Library of checks: pure logic, no transport, no database | Python 3.12, uv |
| `backend/` | REST API, persistence, orchestration; imports `algorithms` | Python 3.12, FastAPI, uv, PostgreSQL, S3 |
| `model/` | Research, training, evaluation (not deployed, never imported) | Python, Jupyter |
| `frontend/` | Web UI | React 19, TypeScript, Vite, yarn |
| `docs/` | Documentation for **humans** (mostly Russian) | Markdown |
| `weights/` | Model weights, one subdirectory per model family (`weights/easyocr/`). Only `.gitkeep` files are committed; docker mounts it | - |
| `.context/` | Additional context for **agents** | Markdown |
| `.github/workflows/` | CI per project, release image builds, Claude review | GitHub Actions |

There is no `pyproject.toml` at the repository root: every Python project owns its own `pyproject.toml`
and `uv.lock`. Run commands from the project directory or through the root `justfile`
(`just backend run`, `just algorithms check`).

## Architecture

```
frontend --REST--> backend --imports--> algorithms
                      |
          PostgreSQL 18 + S3 (RustFS)      (later: gRPC interface for ЧЗ services, a second adapter over the same service layer)
```

- `algorithms` knows nothing about HTTP, gRPC, databases or the backend. It exposes checks that take a
  `ProductCard` and return a `CheckResult`.
- `backend` never implements check logic. It stores cards and photos, runs checks through `CheckRunner`,
  and serves results. REST handlers and any future gRPC servicer are thin adapters over `services/`.
- `model/` produces weights and experiments. Neither `algorithms` nor `backend` imports from it.
- Full stack: `docker compose up --build` (config from `.env`, template in `.env.example`).

## Where code goes

Place code by what it needs, not by what is easiest to write. Unsure -> ask before writing.

| Code | Home |
|---|---|
| A check: rule, validator, parser, text comparison, classical CV, running a trained model for a check | `algorithms/` |
| Endpoints, request/response schemas, persistence, file storage, running checks, settings | `backend/` |
| Training, evaluation, research, model export | `model/` |

- Check logic never goes into `backend/`, even as a "quick fix". If the backend needs a new check, add it
  to `algorithms/` and register it.
- `algorithms` must not import `backend`, `model` or any web/database framework.
- No new top-level project or directory with its own server or Dockerfile without asking.
- There is one result vocabulary: `CheckStatus` and `CheckResult` from `carat_algorithms.core`. Do not
  invent per-check status names, score scales or verdict enums.

## Python rules (all Python projects)

- Python **3.12**, **uv** only (`uv add`, `uv sync`, `uv lock`). Never `pip install`, never a hand-made venv.
  Commit `uv.lock` together with `pyproject.toml`.
- Type hints on every function and method, parameters and return type. Modern syntax: `list[str]`,
  `X | None`, `collections.abc`. `pyright` must pass.
- `ruff` for linting and formatting, `pytest` for tests. `just check` runs all three and must pass
  before every commit.
- Names: `snake_case` for modules, functions and variables, `PascalCase` for classes, `UPPER_SNAKE_CASE`
  for constants and reason codes. Descriptive names only: no single-letter variables except loop counters.
- Logging through `logging`, never `print`. Never log product data, request payloads or photos.
- Paths through `pathlib.Path`. Configurable values come from settings or env vars, not constants scattered in code.

## Tools and skills

- there is a `.agents/skills` directory with predefined skills for this project. it is symlinked
  to `.claude/skills` and `.codex/skills` for those specific agents to be able to use those skills
- **graphify**: if a code graph exists, query it (report/graph) before broad grep/glob exploration,
  and use it to find callers and dependencies across projects. Rebuild it after large structural changes.
- **context-manager**: use it for complex or multi-session work (large features, refactors,
  investigations) to keep plans and progress in `.context/` so the next session can resume.
- **stop-slop**: use this skill when writing lots of text: documentation, pull request description, etc.
- **caveman**: use this skill when working on lots of text. pair it together with context-manager to
  save tokens.
- **investigate-first**: use this skill when planning, exploring or explaining the project to the user
- Put agent-facing notes in `.context/`, never in `docs/`. Edit `docs/` only when asked.

## Git workflow

Never commit to `master` or `dev` directly. All work goes through a PR into `dev`;
`dev -> master` is done only by Maintainers.

1. Start from fresh `dev`: `git fetch origin && git checkout dev && git pull --ff-only`.
2. Create a branch: `git switch -c <prefix>/<short-kebab-description>` (2-5 lowercase words).
   Prefixes: `feature/`, `fix/`, `refactor/`, `chore/`, `docs/`
3. If already on a branch, check it is the right one and up to date: `git fetch origin` and
   `git rebase origin/dev` when behind. Use `git push --force-with-lease` only on your own branch.
4. Commits: small, one logical change each. Title in English, imperative, capitalized, no period,
   <= 50 chars (`Add GTIN validation check`, `Fix crash on empty photo`)
5. Stage files by name, not `git add .`; check `git status` and `git diff --staged` first.
6. PR into `dev`: same title rules (it becomes the squash commit), description with what/why/how
   to test, Taiga task link in the body (not `#123` in the title). One PR = one task.
7. Run `just check` for every affected project before pushing.
8. Do not merge PRs, approve your own work, or delete remote branches - humans do that.
9. Before opening a PR or when asked to review a PR - check the diff/code in the PR against `REVIEW.md`,
   which contains review instruction and rules

When working with worktrees, keep them in `.worktrees/` directory with directory name derived from
branch's name (e.g.: `feature/auth` branch will be in `.worktrees/feature-auth` worktree)

## Guardrails

- **No secrets.** Never commit `.env`, tokens, keys or credentials. Config goes through env vars.
- **No large files.** Never commit model weights (`*.pth`, `*.safetensors`, `*.onnx`, ...), datasets, CSV
  dumps, archives or build output. Document the download source and target path in that
  project's `README.md` instead. If you do not know where a file came from, ask the user.
- **No generated code** in git: `dist/`, `__pycache__/`, `.venv/`, coverage output.
- **Agent instruction files** (`AGENTS.md`, `CLAUDE.md`) are edited only after a **critical**
  change to the repo (new project, new build tool, changed workflow), or when explicitly asked to
  - never automatically
- **CI, release and Docker** (`.github/workflows/`, `Dockerfile`s, `docker-compose.yml`,
  `.dockerignore`) are edited only when the task is about them or a critical change requires it.
- **Versions.** The project version lives in `backend/pyproject.toml`, `algorithms/pyproject.toml` and
  `frontend/package.json`. Bump them together and only when asked.
- **Organization.** Keep the existing clean, explicit layout: clear module and package names, one
  responsibility per module, no junk dirs (`utils2`, `new`).
- **Scope.** Change only what the task needs. No repo-wide reformatting, no unrelated renames.
- **Dependencies.** Add them through the project's package manager (uv, yarn) and commit the lockfile.
  Do not add new tools, frameworks or services without asking.
- **Tests.** Never delete or weaken a test to make a change pass. If a test is wrong, say so and fix it openly.
- **Flag violations.** Check every request and your own plan against this file, the project
  `AGENTS.md` and `REVIEW.md`. If the user asks for, or is doing, something that breaks them
  (misplaced code, new service, check logic in the backend, `async def` handler, commit to `dev`,
  committed weights...), say so **before acting**: name the rule, why, and a compliant alternative.
  Never comply silently. If they still insist, do it and note the deviation in the PR description.
- **Destructive actions** (history rewrites on shared branches, deleting files or data, dropping
  DB tables, resetting volumes) require explicit user confirmation.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
