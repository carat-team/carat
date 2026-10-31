# carat-backend

The Carat REST API. It stores product cards and their photos in PostgreSQL, runs the checks from
[carat-algorithms](../algorithms/README.md) on a card, and returns one result per check to the frontend.

The backend contains no check logic. To change how a card gets judged, edit `algorithms/`.

## Setup

You need [uv](https://docs.astral.sh/uv/) and [just](https://just.systems/). uv installs Python 3.12 and pulls in
`algorithms/` from the same repository as an editable dependency, so your edits there show up without reinstalling.

```sh
cd backend
just sync    # install dependencies
just run     # start the API on http://localhost:8080
just check   # lock check, ruff, pyright, pytest
```

Check that the server answers: `curl http://localhost:8080/health` returns `{"status":"ok"}`.

From the repository root the same recipes run as `just backend <recipe>`.

| Recipe | What it does |
|---|---|
| `sync` | Install dependencies |
| `run` | Start uvicorn with one worker |
| `lint` / `fix` | Check / apply ruff linting and formatting |
| `typecheck` | `pyright` in strict mode |
| `test` | `pytest` |
| `check` | All of the above plus `uv lock --check`. Run it before every commit |
| `migrate` | Apply database migrations |
| `migrate-new "<message>"` | Generate a migration from model changes. Read the generated file before you commit it |

## Configuration

All settings come from environment variables, read in `src/carat_backend/settings.py`. `just` loads a `.env` file
when it finds one. The repository root has `.env.example` with every variable; copy it to `.env` and fill it in.

| Variable | Default | Meaning |
|---|---|---|
| `CHECK_CONCURRENCY` | `2` | How many cards can run their checks at the same time |

## API

[docs/api.md](../docs/api.md) defines the contract with the frontend: the card fields, the endpoints, the check
result format and the 422 validation error. Agree changes with the frontend team first.

## How checks run

`POST /api/products/{id}/check` builds a `ProductCard` from the stored product and hands it to `CheckRunner`
(`src/carat_backend/services/check_runner.py`). The runner calls every check from the algorithms registry:

- When a check raises, the runner records an `ERROR` result with reason code `CHECK_CRASHED` for that check and
  carries on. One broken check never fails the whole request.
- The runner returns results unchanged. The backend does not rename, merge or reinterpret statuses.
- Logs contain the check id, status and duration, never card contents.

## Design choices

- **One uvicorn worker.** Model-based checks load their weights into memory. A second worker would load them
  twice. The `justfile` and the Dockerfile both pin `--workers 1`.
- **Plain `def` handlers.** Checks block the CPU. FastAPI runs `def` handlers in a thread pool, while an
  `async def` handler would block the event loop for every other request.
- **A concurrency limit.** `CHECK_CONCURRENCY` caps how many cards run checks at once, so a burst of requests
  cannot exhaust memory.
- **Layers.** `api/` (routers and schemas) calls `services/` (CheckRunner, product and photo logic), which calls
  `storage/` (database models, repositories, photo files). Another transport, such as gRPC for Честный Знак
  services, sits next to `api/` and calls the same services.

## Tests

API tests go through FastAPI's `TestClient`. Tests that need the database run against a real PostgreSQL (the
compose service or `TEST_DATABASE_URL`), because SQLite handles JSONB differently. Check logic is tested in
`algorithms/`; the backend tests cover the runner and the API.
