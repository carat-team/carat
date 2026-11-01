# AGENTS.md

Instructions for AI agents in the Carat repository. `CLAUDE.md` is a symlink to this file. Each project has its own
`AGENTS.md`; read it before touching that directory.

## What Carat is

Carat checks product cards for the "Честный Знак" (ЧЗ) marking system. A card is attributes (name,
brand, perfumery type, volume, TN VED code, GTIN, ...) plus photos. Carat runs independent checks and returns one
result per check: `PASS`, `WARNING`, `REVIEW`, `NOT_CHECKED` or `ERROR`, with a reason code and an explanation. It
never accepts or rejects a card; the consumer (our frontend, later ЧЗ services) applies its own policy.

Carat started as a fork of Cogniflex (AI-content detection), kept under the tag `legacy/java-backend`. Never port 
AI-content detection back.

## Repository map

| Path | What | Stack |
|---|---|---|
| `algorithms/` | Checks: pure logic, no transport, no database | Python 3.12, uv |
| `backend/` | REST API, persistence, orchestration; imports `algorithms` | Python 3.12, FastAPI, PostgreSQL, S3 |
| `model/` | Research, training, evaluation; not deployed, never imported | Python, Jupyter |
| `frontend/` | Web UI | React 19, TypeScript, Vite, yarn |
| `docs/` | Documentation for humans (mostly Russian) | Markdown |
| `weights/` | Model weights, one subdirectory per family; only `.gitkeep` committed, docker mounts it | - |
| `.context/` | Notes for agents | Markdown |
| `.github/workflows/` | CI per project, release images, Claude review | GitHub Actions |

No root `pyproject.toml`: each Python project owns its `pyproject.toml` and `uv.lock`. Run commands from the project
directory or through the root `justfile` (`just backend run`, `just algorithms check`).

## Architecture

- `algorithms` knows nothing about HTTP, gRPC, databases or the backend: a check takes a `ProductCard` and returns
  a `CheckResult`.
- `backend` never implements check logic. It stores cards and photos and runs checks through `CheckRunner`. REST
  handlers (and a future gRPC servicer) are thin adapters over `services/`.
- Full stack: `docker compose up --build` (config from `.env`, template `.env.example`).

## Where code goes

| Code | Home |
|---|---|
| A check: rule, validator, parser, text comparison, classical CV, running a trained model | `algorithms/` |
| Endpoints, schemas, persistence, file storage, running checks, settings | `backend/` |
| Training, evaluation, research, model export | `model/` |

- Check logic never goes into `backend/`, not even as a quick fix: add it to `algorithms/` and register it.
- `algorithms` never imports `backend`, `model` or a web/database framework.
- One result vocabulary: `CheckStatus` and `CheckResult` from `carat_algorithms.core`. No per-check statuses,
  score scales or verdict enums.
- No new top-level project, server or Dockerfile without asking. Unsure where code goes: ask first.

## Python rules

- Python 3.12, uv only (`uv add`, `uv sync`, `uv lock`); never `pip install` or a hand-made venv. Commit `uv.lock`
  with `pyproject.toml`.
- Type hints on every function, modern syntax (`list[str]`, `X | None`, `collections.abc`); pyright strict passes.
- ruff, pyright and pytest through `just check`, which must pass before every commit.
- `snake_case` modules, functions, variables; `PascalCase` classes; `UPPER_SNAKE_CASE` constants and reason codes.
  Descriptive names, no single letters except loop counters.
- `logging`, never `print`. Never log product data, request payloads or photos.
- `pathlib.Path` for paths. Configurable values come from settings, not constants scattered in code.

## Writing style

Applies to code, comments, docs, commits and PR text:

- No single-character arrows (`→`, `⇒`, `←`); write `->` or `<-`.
- No em or en dashes (`—`, `–`); write `-`.
- No `«»` in code and comments; use `"` or `'`.

## Tools and skills

Project skills live in `.agents/skills` (symlinked to `.claude/skills` and `.codex/skills`).

- **graphify**: when `graphify-out/graph.json` exists, start with `graphify query "<question>"` (`path`, `explain`
  for relationships) before grepping; `GRAPH_REPORT.md` only for broad architecture. Run `graphify update .` after
  code changes.
- **context-manager** with **caveman**: plans and progress of multi-session work in `.context/`.
- **stop-slop**: for documentation and PR descriptions.
- **investigate-first**: when planning, exploring or explaining the project.
- Agent notes go to `.context/`, never `docs/`. Edit `docs/` only when asked.

## Git workflow

Never commit to `master` or `dev`. All work goes through a PR into `dev`; `dev -> master` is for maintainers.

1. Branch from fresh `dev` (`git fetch origin && git checkout dev && git pull --ff-only`):
   `git switch -c <prefix>/<short-kebab-description>`, prefixes `feature/`, `fix/`, `refactor/`, `chore/`, `docs/`.
2. On an existing branch: check it is the right one, `git rebase origin/dev` when behind; `--force-with-lease` only
   on your own branch.
3. Small commits, one logical change each. Title in English, imperative, capitalized, no period, <= 50 characters.
4. Stage files by name, not `git add .`; check `git status` and `git diff --staged` first.
5. PR into `dev`: same title rules, description with what/why/how to test and the Taiga link. One PR = one task.
6. Run `just check` for every affected project before pushing. Check the diff against `REVIEW.md` before opening
   or reviewing a PR.
7. Never approve your own work or delete remote branches.

Worktrees go to `.worktrees/<branch-name-with-dashes>` (`feature/auth` -> `.worktrees/feature-auth`).

## Guardrails

- **No secrets**: never commit `.env`, tokens, keys or credentials.
- **No large files**: no weights (`*.pth`, `*.safetensors`, `*.onnx`, ...), datasets, CSV dumps, archives or build
  output. Document the download source and target path in the project README; ask when the origin is unknown.
- **No generated code**: `dist/`, `__pycache__/`, `.venv/`, coverage output.
- **Agent files** (`AGENTS.md`, `CLAUDE.md`) change only after a critical repo change or when asked.
- **CI, release and Docker** files change only when the task is about them or a critical change requires it.
- **Versions** live in `backend/pyproject.toml`, `algorithms/pyproject.toml`, `frontend/package.json`; bump them
  together and only when asked.
- **Layout**: clear module names, one responsibility per module, no junk dirs (`utils2`, `new`).
- **Scope**: change only what the task needs; no repo-wide reformatting or unrelated renames.
- **Dependencies** through the package manager with the lockfile; no new tools, frameworks or services without asking.
- **Tests**: never delete or weaken a test to make a change pass; fix a wrong test openly.
- **Destructive actions** (history rewrites on shared branches, deleting files or data, dropping tables, resetting
  volumes) need explicit confirmation.
- **Flag violations**: check every request and your own plan against this file, the project `AGENTS.md` and
  `REVIEW.md`. If something breaks them, say so before acting: the rule, why, and a compliant alternative. If the
  user insists, do it and note the deviation in the PR description.
