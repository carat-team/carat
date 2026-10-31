# backend/AGENTS.md

REST API, persistence and orchestration. Read the root `AGENTS.md` first; this file adds rules for `backend/` only.
Package `carat_backend`, Python 3.12, uv, `src/` layout. Human-facing overview and rationale: `README.md`.

No check logic here. An `if` that decides whether a card is good belongs in `algorithms/`.

## Stack

FastAPI + Pydantic v2, uvicorn (one worker), pydantic-settings, PostgreSQL 18 with SQLAlchemy 2 (sync),
psycopg 3 and Alembic. Tests: pytest + `TestClient` (needs `httpx2`) on real PostgreSQL. Quality: ruff, pyright,
`just check`. No Redis, Celery or message broker without asking.

## Layout

```
backend/
  alembic.ini, migrations/
  src/carat_backend/
    main.py        create_app(), router wiring
    settings.py    pydantic-settings
    api/           routers, request/response schemas, error handlers. Thin
    services/      CheckRunner, product service, photo service
    storage/       SQLAlchemy models, repositories, photo file storage
  tests/
```

- Dependency direction: `api/` -> `services/` -> `storage/`. `api/` never touches SQLAlchemy sessions.
- A future gRPC servicer is a second adapter next to `api/`, calling the same `services/`.

## Handlers

- Plain `def` handlers only, never `async def`.
- One uvicorn worker (`--workers 1` in `justfile` and Dockerfile `CMD`). Do not change without asking.
- Check runs go through the `CHECK_CONCURRENCY` semaphore (default 2).
- A handler parses input, calls one service method, returns a schema. No business logic.

## API

- Contract: `docs/api.md`. Endpoints: `GET/POST /api/products`, `GET/PATCH /api/products/{id}`,
  `POST /api/products/{id}/photos` (multipart `file`, `perspective`, `packageId`),
  `DELETE /api/products/{id}/photos/{photoId}`, `POST /api/products/{id}/check`.
- 422 body is exactly `{"error": "VALIDATION_ERROR", "fields": {"<field>": "<message>"}}`. Do not change it
  without telling the frontend team.
- Return check results as `carat_algorithms` produces them. Never rename, merge or reinterpret statuses.

## CheckRunner

- Runs every check from `carat_algorithms.core.get_checks()` on a `ProductCard` built from the stored product.
- Catches every exception: `ERROR`, reason code `CHECK_CRASHED`, the check's id and `algorithm_version`.
- Logs check id, status and duration only. Never card contents or tracebacks with values.
- Store `algorithm_version` with each result.

## Database

- Tables: `products`, `product_attributes` (JSONB `attributes`), `product_photos`. New card fields need no
  migration; schema changes go through Alembic.
- Never edit a merged migration; add a new one with `just backend migrate-new "<message>"` and read it.
- Repositories return domain objects or Pydantic models, never live ORM instances, across the `services/` boundary.
- Tests use real PostgreSQL (compose or `TEST_DATABASE_URL`). No SQLite.

## Photos

- Files under `PHOTO_STORAGE_DIR`; the database keeps metadata and a relative path.
- Validate content type and size at the boundary. Generate stored names; never trust the client name.
- Never commit photos, including test photos over 100 KB.

## Settings

- All config in `settings.py`. No `os.environ` reads elsewhere.
- Every variable listed in the root `.env.example` with a safe placeholder; `.env` never committed.
- Document each new variable in the `README.md` configuration table.

## Tests

- API tests via `TestClient`; service tests against the test database.
- Runner tests use fake checks (one passing, one raising).
- Do not re-test check logic; that lives in `algorithms/tests/`.
- Never delete or weaken a test to make a change pass.
