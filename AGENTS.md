# AGENTS.md

Instructions for AI agents working in the Carat repository. `CLAUDE.md` is a symlink to this file.
Each service has its own `AGENTS.md` with stack, build and style rules - read it before touching that directory.

## What Carat is

Carat checks product card submissions (text fields and product photos) sent to the "Честный Знак"
marking system and flags or filters suspicious, low-quality or inconsistent cards. It grew out of
Cogniflex, an AI-generated content detector: the analysis core is reused, the use case is new.
The project is early-stage - concrete text/image checks, the frontend and the final API are still evolving.

Every item goes through two analysis paths whose results are fused into one verdict:
- **Static** - deterministic rules over the content (text heuristics, image checks) -> evidence + score.
- **Dynamic** - ML models served by the inference service over gRPC -> class + confidence.

## Repository map

| Path | What | Stack |
|---|---|---|
| `backend/` | REST API, all static analysis, analysis pipeline, persistence | Java 25, Spring Boot 4, Gradle |
| `inference/` | gRPC model-serving service | Python 3.12, uv, just, PyTorch (CPU) |
| `model/` | Research, training, evaluation (not deployed) | Python, Jupyter |
| `frontend/` | Web UI (early, not in Docker Compose yet) | React 19, TypeScript, Vite, yarn |
| `proto/carat/inference/` | gRPC contract, single source of truth | Protobuf 3 |
| `docs/` | Documentation for **humans** (mostly Russian) | Markdown |
| `.context/` | Additional context for **agents** | Markdown |
| `.github/workflows/` | CI tests, release image builds, Claude review | GitHub Actions |

## Architecture

```
frontend --REST--> backend --gRPC(:50051)--> inference
                      |
              PostgreSQL 18 + Redis 8
```

- `backend` preprocesses input, runs static and dynamic analyzers in parallel, fuses scores,
  stores history in PostgreSQL (Flyway migrations) and rate-limits via Redis.
- `inference` loads model weights from `inference/weights/` at startup and answers `AnalyzeText` /
  `AnalyzePhoto` / `AnalyzeVideo` RPCs. It never calls the backend.
- Both sides generate code from `proto/` at build time; generated code is never committed.
  A proto change must keep backend and inference compiling in the same PR.
- `model/` produces weights; the result is shipped to `inference/weights/` manually, never via imports.
- Full stack: `docker compose up --build` (config from `.env`, template in `.env.example`).

## Where code goes

Place code by what it needs, not by what is easiest to write. Unsure -> ask before writing.

| Code | Home |
|---|---|
| Static logic: rules, heuristics, validators, parsers, dictionary/grammar scans, classical CV without a learned model | `backend/`, **Java** |
| Endpoints, orchestration, data preparation, persistence | `backend/`, **Java** |
| Running a trained model (weights, preprocessing for it, forward pass) | `inference/` |
| Training, evaluation, research, export of models | `model/` |

- Static logic never goes into `inference/`, `model/` or a new service, even if prototyped in Python.
  A Python prototype may live in `model/notebooks/`, but the deliverable is Java in `backend/`.
- A feature mixing endpoint, static logic and a model is split along the table: backend owns the
  endpoint, static part and data preparation, then calls inference over gRPC (new RPC in `proto/`);
  inference owns only the model call. Not a separate microservice, not everything on one side.
- No new top-level service or directory with its own server or Dockerfile.
- Backend is always Java. Never Python "because it is quicker"; porting a prototype means rewriting it in Java.

## Tools and skills

- there is a `.agents/skills` directory present with predefined skills for this project. it is symlinked
  to `.claude/skills` and `.codex/skills` for those specific agents to be able to use those skills
- **graphify**: if a code graph exists, query it (report/graph) before broad grep/glob exploration,
  and use it to find callers and dependencies across services. Rebuild it after large structural changes.
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
   <= 50 chars (`Add GTIN validation rule`, `Fix crash on empty photo`)
5. Stage files by name, not `git add .`; check `git status` and `git diff --staged` first.
6. PR into `dev`: same title rules (it becomes the squash commit), description with what/why/how
   to test, Taiga task link in the body (not `#123` in the title). One PR = one task.
7. Run the affected service's build, tests and linters before pushing.
8. Do not merge PRs, approve your own work, or delete remote branches - humans do that.
9. Before opening a PR or when asked to review a PR - check the diff/code in the PR against `REVIEW.md`,
   which contains review instruction and rules

When working with worktrees, keep them in `.worktrees/` directory with directory name derived from
branch's name (e.g.: `feature/auth` branch will be in `.worktrees/feature-auth` worktree)

## Guardrails

- **No secrets.** Never commit `.env`, tokens, keys or credentials. Config goes through env vars.
- **No large files.** Never commit model weights (`*.pth`, `*.safetensors`, ...), datasets, CSV
  dumps, archives or build output. Document the download source and target path in that
  service's `README.md` instead. If you do not know where a file came from, ask the user.
- **No generated code** in git: `inference/generated/`, `backend/build/`, `frontend/dist/`.
- **Agent instruction files** (`AGENTS.md`, `CLAUDE.md`) are edited only after a **critical**
  change to the repo (new service, new build tool, changed workflow), or when explicitly asked to
  - never automatically
- **CI, release and Docker** (`.github/workflows/`, `Dockerfile`s, `docker-compose.yml`,
  `.dockerignore`) are edited only when the task is about them or a critical change requires it.
- **Versions.** The project version lives in `backend/build.gradle`, `inference/pyproject.toml` and
  `frontend/package.json`. Bump them together and only when asked.
- **Organization.** Keep the existing clean, explicit layout (like `proto/carat/inference/`):
  clear module and package names, one responsibility per module, no junk dirs (`utils2`, `new`).
- **Scope.** Change only what the task needs. No repo-wide reformatting, no unrelated renames.
- **Dependencies.** Add them through the service's package manager (Gradle, uv, yarn) and commit
  the lockfile. Do not add new tools, frameworks or services without asking.
- **Flag violations.** Check every request and your own plan against this file, the service
  `AGENTS.md` and `REVIEW.md`. If the user asks for, or is doing, something that breaks them
  (misplaced code, new service, Python in backend, commit to `dev`, committed weights...), say so
  **before acting**: name the rule, why, and a compliant alternative. Never comply silently. If they
  still insist, do it and note the deviation in the PR description.
- **Destructive actions** (history rewrites on shared branches, deleting files or data, dropping
  DB tables, resetting volumes) require explicit user confirmation.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
