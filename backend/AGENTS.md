# backend/AGENTS.md

REST API, persistence and orchestration. Read the root `AGENTS.md` first. This file adds rules for
`backend/` only. Package name: `carat_backend`. Python 3.12, uv, `src/` layout.

The backend stores product cards and photos, runs checks from `carat_algorithms`, and serves results.
It never implements check logic. If you want to write an `if` that decides whether a card is good,
it belongs in `algorithms/`.

## Stack

| Concern | Choice |
|---|---|
| Web | FastAPI, Pydantic v2, uvicorn (one worker) |
| Settings | pydantic-settings, all config from env, template in `.env.example` |
| Database | PostgreSQL 18, SQLAlchemy 2 (sync), psycopg 3, Alembic |
| Tests | pytest, httpx `TestClient`, real PostgreSQL |
| Quality | ruff, pyright, `just check` |

No Redis, no Celery, no message broker. Do not add any without asking.

## Layout

```
backend/
  pyproject.toml
  uv.lock
  alembic.ini
  migrations/
  src/carat_backend/
    main.py                 app factory, router wiring
    settings.py             pydantic-settings
    api/                    routers, request/response schemas, error handlers. Thin.
    services/               CheckRunner, product service, photo service
    storage/                SQLAlchemy models, repositories, photo file storage
  tests/
```

Dependency direction: `api/` -> `services/` -> `storage/`. Never the other way. `api/` does not touch
SQLAlchemy sessions directly. A future gRPC servicer is a second adapter next to `api/`, calling the same `services/`.

## Handlers

- **Plain `def` handlers only. Never `async def`.** Checks are CPU-bound and blocking; an `async def`
  handler would freeze the event loop. FastAPI runs plain `def` handlers in a thread pool.
- **One uvicorn worker** (`--workers 1`). Models are loaded in-process and must not be duplicated.
  This is fixed in the `justfile` and in the Dockerfile `CMD`. Do not change it without asking.
- Heavy checks (vision, ML) run behind a semaphore sized by `CHECK_CONCURRENCY` (default 2).
  Light text checks do not need it.
- Handlers parse input, call one service method, return a schema. No business logic in them.

## API

Contract is defined in `docs/api.md` (derived from the MVP sheet). Current surface:

- `GET /api/products`, `POST /api/products`
- `GET /api/products/{id}`, `PATCH /api/products/{id}`
- `POST /api/products/{id}/photos` (multipart: `file`, `perspective`, `packageId`)
- `DELETE /api/products/{id}/photos/{photoId}`
- Checks: `POST /api/products/{id}/check` returns one `CheckResult` per registered check

Validation errors return HTTP 422 with exactly `{"error": "VALIDATION_ERROR", "fields": {"<field>": "<message>"}}`.
Do not change this shape without telling the frontend team.

Check results are returned as produced by `carat_algorithms` (`check_id`, `status`, `reason_code`,
`explanation`, `field_refs`, `algorithm_version`). The backend does not rename, merge or reinterpret statuses.

## CheckRunner

- Runs every registered check against a `ProductCard` built from the stored product.
- Catches **every** exception from a check and records `ERROR` with reason code `CHECK_CRASHED`
  and the check id. One crashing check never fails the whole request.
- Never logs card contents. It logs check id, status and duration.
- Records `algorithm_version` with each result so old results stay explainable.

## Database

- Products use one `products` table plus `product_attributes` (JSONB `attributes` per product) and
  `product_photos`. New card fields need no migration; schema changes still go through Alembic.
- **Never edit a migration that was already merged.** Add a new one. Generate with
  `just backend migrate-new "<message>"` and read the generated file before committing.
- Repositories return domain objects or Pydantic models, not live ORM instances, across the `services/` boundary.
- Tests run against a real PostgreSQL (docker compose service or `TEST_DATABASE_URL`). No SQLite substitute:
  JSONB behaviour differs.

## Photos

- Files live on a mounted volume under `PHOTO_STORAGE_DIR`. The database stores metadata and a relative path only.
- Validate content type and size at the boundary. Never trust the client file name; generate the stored name.
- Never commit photos, including test photos larger than 100 KB.

## Settings and secrets

- Everything configurable comes from `settings.py`. No `os.environ` reads elsewhere.
- `.env` is never committed; `.env.example` lists every variable with a safe placeholder.

## Tests

- API tests go through `TestClient`; service tests call the service with a test database.
- Test the runner with fake checks (one passing, one raising) to prove `ERROR` isolation.
- Do not re-test check logic here; that belongs to `algorithms/tests/`.
- Never delete or weaken a test to make a change pass.
