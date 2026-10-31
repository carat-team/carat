# backend/AGENTS.md

REST API, persistence and orchestration. Read the root `AGENTS.md` first; this file adds rules for `backend/` only.
Package `carat_backend`, Python 3.12, uv, `src/` layout. Human-facing overview and rationale: `README.md`.

No check logic here. An `if` that decides whether a card is good belongs in `algorithms/`.

## Stack

FastAPI + Pydantic v2, uvicorn (one worker), pydantic-settings, PostgreSQL 18 with SQLAlchemy 2 (sync),
psycopg 3 and Alembic, S3-compatible object storage through the `minio` client (RustFS locally).
Tests: pytest + `TestClient` (needs `httpx2`) on real PostgreSQL and RustFS. Quality: ruff, pyright, `just check`.
No Redis, Celery or message broker without asking.

## Layout

```
backend/
  settings.toml, alembic.ini, migrations/
  src/carat_backend/
    main.py          uvicorn entry point (re-exports rest.app.create_app)
    settings.py      settings.toml + DB_* / S3_* environment
    bootstrap.py     Services + build_services(settings): the only place services are built
    domain/          models.py, errors.py: shared by every layer and adapter
    services/        products.py, photos.py, checks.py (CheckRunner + CheckService)
    storage/         database.py, tables.py, repositories/, object_store.py
    rest/            app.py, dependencies.py, errors.py, routers/ (one module per resource), schemas/
  tests/
```

- Dependency direction: `rest/` -> `services/` -> `storage/`; `domain/` is imported by all of them.
- `rest/` never touches SQLAlchemy or the object store. Services never import FastAPI or schemas.
- Services take and return `domain` models and raise `domain.errors`; adapters map them to their transport.
- A future gRPC adapter lives in `carat_backend/grpc/` and gets its services from `build_services()`.
  Do not add it, a proto file or a grpc dependency without asking.

## Handlers

- Plain `def` handlers only, never `async def`.
- One uvicorn worker (`--workers 1` in `justfile` and Dockerfile `CMD`). Do not change without asking.
- Check runs go through the `[checks] concurrency` semaphore.
- A handler parses input, calls one service method, returns a schema. No business logic.
- Request/response schemas live in `rest/schemas/<resource>.py`; routers in `rest/routers/<resource>.py`.

## API

- Contract: `docs/api.md` (from the MVP sheet). Bodies wrap card fields in `{"attributes": {...}}`.
- Validation is format only (types, lengths, patterns, units); any attribute may be missing in a draft.
- 422 body is exactly `{"error": "VALIDATION_ERROR", "fields": {"<field path>": "<Russian message>"}}`.
  Do not change it without telling the frontend team.
- Return check results as `carat_algorithms` produces them. Never rename, merge or reinterpret statuses.

## CheckRunner

- Runs every check from `carat_algorithms.core.get_checks()` on a `ProductCard` built from the stored product.
- Catches every exception: `ERROR`, reason code `CHECK_CRASHED`, the check's id and `algorithm_version`.
- Logs check id, status and duration only. Never card contents or tracebacks with values.

## Database

- EAV: `products` (id, status, timestamps), `product_attributes` (product_id, attribute_key, value_json JSONB,
  primary key on both ids), `product_photos` (metadata + `object_key`). New attributes need no migration.
- Schema changes: edit `storage/tables.py`, `just backend migrate-new "<message>"`, read and fix the file.
- Never edit a merged migration; add a new one. Files use the dated `file_template` from `alembic.ini`.
- Repositories return `domain` models, never ORM rows.
- Tests use real PostgreSQL via `TEST_DATABASE_URL` (`just backend test-services`); without it they skip. No SQLite.

## Photos

- Bytes in the object store under `products/<product_id>/<photo_id>.<ext>`; the database keeps metadata only.
- Validate content type (JPEG, PNG, WEBP) and size at the boundary. Never use the client's file name.
- Upload writes the object first and removes it if the row fails; delete removes the row first.
- Never commit photos, including test photos over 100 KB.

## Settings

- Non-secret settings in `settings.toml` sections; secrets only from env: `DB_*` and `S3_*`, no prefix, no nesting.
- All config goes through `settings.py`. No `os.environ` reads elsewhere.
- Model weights: one `[weights] <model>_dir` entry per model family, pointing at `weights/<model>/`.
- New env variables go to the root `.env.example`; new settings of either kind go to the `README.md` table.

## Tests

- API tests via `TestClient` against the test services; settings tests use temporary TOML files.
- Runner tests use fake checks (one passing, one raising).
- Do not re-test check logic; that lives in `algorithms/tests/`.
- Never delete or weaken a test to make a change pass.
