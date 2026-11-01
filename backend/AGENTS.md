# backend/AGENTS.md

REST API, persistence and orchestration; adds to the root `AGENTS.md`. Package `carat_backend`, Python 3.12, uv,
`src/` layout. Human overview and rationale: `README.md`.

No check logic here: an `if` that decides whether a card is good belongs in `algorithms/`.

## Stack

FastAPI + Pydantic v2, uvicorn (one worker), pydantic-settings, PostgreSQL 18 with SQLAlchemy 2 (sync), psycopg 3
and Alembic, S3-compatible storage through the `minio` client (RustFS locally). Tests: pytest + `TestClient` (needs
`httpx2`) on real PostgreSQL and RustFS. No Redis, Celery or message broker without asking.

## Layout

```
backend/
  settings.toml, alembic.ini, migrations/, Dockerfile
  src/carat_backend/
    main.py          uvicorn entry point (re-exports rest.app.create_app)
    settings.py      settings.toml + DB_* / S3_* / WEIGHTS_DIR environment
    bootstrap.py     build_services(settings): the only place services are built
    domain/          models.py, errors.py: shared by every layer and adapter
    services/        products.py, photos.py, checks.py (CheckRunner + CheckService)
    storage/         database.py, tables.py, repositories/, object_store.py
    rest/            app.py, dependencies.py, errors.py, routers/, schemas/ (one module per resource)
  tests/
```

- `rest/` -> `services/` -> `storage/`; `domain/` is shared. `rest/` never touches SQLAlchemy or the object store;
  services never import FastAPI or schemas.
- Services take and return `domain` models and raise `domain.errors`; adapters map them to their transport.
- A future gRPC adapter goes to `carat_backend/grpc/` and uses `build_services()`. No grpc code, proto or
  dependency without asking.

## Handlers

- Plain `def` handlers, never `async def`. One uvicorn worker (`--workers 1` in `justfile` and Dockerfile); do not
  change without asking.
- A handler parses input, calls one service method and returns a schema. No business logic.
- Photo loading and check runs go through the `[checks] concurrency` semaphore.

## API

- Contract: `docs/api.md`. Bodies wrap card fields in `{"attributes": {...}}`.
- Validation is format only (types, lengths, patterns, units); any attribute may be missing in a draft.
- 422 body is exactly `{"error": "VALIDATION_ERROR", "fields": {"<field path>": "<Russian message>"}}`; do not
  change it without telling the frontend team.
- Check results go out as `carat_algorithms` produces them; never rename, merge or reinterpret statuses.

## CheckRunner

- Runs every check from `get_checks()` on a `ProductCard` built from the stored product.
- Catches every exception: `ERROR`, reason code `CHECK_CRASHED`, the check's id and `algorithm_version`.
- Logs check id, status and duration only; never card contents or tracebacks with values.

## Database

- EAV: `products`, `product_attributes` (`attribute_key`, `value_json` JSONB), `product_photos` (metadata +
  `object_key`). New attributes need no migration.
- Schema change: edit `storage/tables.py`, `just backend migrate-new "<message>"`, read and fix the file. Never edit
  a merged migration.
- Repositories return `domain` models, never ORM rows.

## Photos

- Bytes in the object store under `products/<product_id>/<photo_id>.<ext>`; the database keeps metadata only.
- Validate content type (JPEG, PNG, WEBP) and size at the boundary; never use the client's file name.
- Upload writes the object first and removes it if the row fails; delete removes the row first.
- Never commit photos; test images stay under 100 KB or are generated in the test.

## Settings

- Connections come only from env: `DB_*`, `S3_*` (no prefix, no nesting) and `WEIGHTS_DIR`. Everything else lives
  in `settings.toml` sections.
- All config goes through `settings.py`; no `os.environ` reads elsewhere.
- Pass `settings.weights.dir` to `algorithms` as is; model code picks its `<family>/` subdirectory. No per-model
  weight settings.
- New env variables go to the root `.env.example`; every new setting goes to the `README.md` table.

## Tests

- API tests via `TestClient` on real PostgreSQL and S3 (`just backend test-services`); without
  `TEST_DATABASE_URL` / `TEST_OBJECT_STORAGE_URL` they skip. No SQLite.
- Settings tests use temporary TOML files; runner tests use fake checks (one passing, one raising).
- Do not re-test check logic; that lives in `algorithms/tests/`.
