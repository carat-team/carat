# carat-backend

The Carat REST API. It stores product cards in PostgreSQL and their photos in S3-compatible object storage, runs
the checks from [carat-algorithms](../algorithms/README.md) on a card, and returns one result per check to the
frontend.

The backend contains no check logic. To change how a card gets judged, edit `algorithms/`.

## Setup

You need [uv](https://docs.astral.sh/uv/), [just](https://just.systems/) and Docker. uv installs Python 3.12 and
pulls in `algorithms/` from the same repository as an editable dependency, so your edits there show up without
reinstalling.

```sh
cd backend
just sync      # install dependencies
just migrate   # create or update the database schema
just run       # start the API on http://localhost:8080
just check     # lock check, ruff, pyright, pytest
```

`just run` and `just migrate` need a PostgreSQL and an S3-compatible server (the project uses
[RustFS](https://github.com/rustfs/rustfs)). Check that the server answers: `curl http://localhost:8080/health`
returns `{"status":"ok"}`.

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
| `migrate-new "<message>"` | Generate a migration from changes in `storage/tables.py` |
| `test-services` / `stop-test-services` | Start / stop a throwaway PostgreSQL and RustFS for the tests |

## Configuration

Settings come from two places:

- **`settings.toml`** in this directory holds everything that is not a secret. Docker mounts its own copy and
  points the `SETTINGS_FILE` variable at it. Relative paths resolve against the directory of the file.
- **Environment variables** hold the database connection and the storage keys. `just` loads them from the root
  `.env` (template: the root `.env.example`), the same file docker compose reads.

| Setting | Where | Default | Meaning |
|---|---|---|---|
| `DB_HOST`, `DB_PORT` | env | `localhost`, `5432` | PostgreSQL server |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | env | `carat`, `carat`, empty | Database and credentials |
| `S3_ACCESS_KEY`, `S3_SECRET_KEY` | env | empty | Object storage credentials |
| `[object_storage] endpoint` | TOML | `localhost:9000` | S3-compatible server, `host:port` |
| `[object_storage] bucket` | TOML | `carat-photos` | Bucket for photos; the backend creates it on first upload |
| `[object_storage] secure` | TOML | `false` | Use HTTPS |
| `[photos] max_size_mb` | TOML | `10` | Larger uploads are rejected with 422 |
| `[weights] easyocr_dir` | TOML | `../weights/easyocr` | EasyOCR weights (see the [algorithms README](../algorithms/README.md#model-weights)) |
| `[checks] concurrency` | TOML | `2` | How many cards can run their checks at the same time |
| `SETTINGS_FILE` | env | `settings.toml` | Path to the TOML file |

Each model family gets its own `[weights]` entry pointing at its directory under the repository's `weights/`.

## API

[docs/api.md](../docs/api.md) defines the contract with the frontend: the card attributes, the endpoints, the
check result format and the 422 validation error. Agree changes with the frontend team first.

## Database and migrations

Cards use an EAV layout: `products` holds one row per card (id, status, timestamps), `product_attributes` one row
per filled attribute (`attribute_key` is the API field name, `value_json` its JSON value), and `product_photos`
the photo metadata. A new card attribute needs no migration, only a field in `rest/schemas/products.py`.

To change the schema:

1. Edit the tables in `src/carat_backend/storage/tables.py`.
2. Run `just migrate-new "Add photo checksum"` against a database that is on the latest migration. Alembic writes
   a file to `migrations/versions/`.
3. Read the file and fix what autogenerate got wrong (renames show up as drop + add), then `just migrate`.

Never edit a migration that is already merged; add a new one.

## How checks run

`POST /api/products/{id}/check` loads the card and its photos and hands a `ProductCard` to `CheckRunner`
(`src/carat_backend/services/checks.py`). The runner calls every check from the algorithms registry:

- When a check raises, the runner records an `ERROR` result with reason code `CHECK_CRASHED` for that check and
  carries on. One broken check never fails the whole request.
- The runner returns results unchanged. The backend does not rename, merge or reinterpret statuses.
- Logs contain the check id, status and duration, never card contents.

## Code layout

```
src/carat_backend/
  main.py        entry point for uvicorn
  settings.py    settings.toml + environment
  bootstrap.py   build_services(settings): builds every service once
  domain/        models (Product, Photo, ProductStatus) and errors shared by all layers
  services/      products, photos, checks (CheckRunner): the behaviour, independent of HTTP
  storage/       tables, repositories, object storage client
  rest/          the REST adapter: app, routers/, schemas/, error handlers, dependencies
```

A request flows `rest/routers` -> `services` -> `storage`. Routers only translate HTTP to a service call and the
result back to a schema; services take and return `domain` models and raise `domain` errors.

## Design choices

- **One uvicorn worker.** Model-based checks load their weights into memory. A second worker would load them
  twice. The `justfile` and the Dockerfile both pin `--workers 1`.
- **Plain `def` handlers.** Checks block the CPU. FastAPI runs `def` handlers in a thread pool, while an
  `async def` handler would block the event loop for every other request.
- **A concurrency limit.** `[checks] concurrency` caps how many cards run checks at once, so a burst of requests
  cannot exhaust memory.
- **Photos in object storage.** The database keeps metadata and an object key; the bytes go to an S3-compatible
  bucket, so the same code runs against RustFS locally and any S3 service in production.
- **Ready for gRPC.** If Честный Знак integrates over gRPC, a `carat_backend/grpc/` package gets a servicer that
  calls the services from `build_services()`, exactly like `rest/app.py` does. Services know nothing about HTTP,
  so nothing below the adapter changes.

## Tests

API tests go through FastAPI's `TestClient` against a real PostgreSQL (SQLite handles JSONB differently) and a real
S3-compatible server. They skip when the services are not configured:

```sh
just test-services        # postgres:18 on port 55432, RustFS on port 59000; prints two export lines
export TEST_DATABASE_URL=postgresql+psycopg://carat:carat@localhost:55432/carat_test
export TEST_OBJECT_STORAGE_URL=http://carat:carat-secret@localhost:59000
just check
just stop-test-services
```

The test session builds the schema by running the migrations, so a broken migration fails the tests. Check logic
is tested in `algorithms/`; the backend tests cover the runner, settings and the API.
