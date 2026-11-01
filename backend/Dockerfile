# Build context: repository root, the backend needs ../algorithms.

FROM ghcr.io/astral-sh/uv:0.13.6-python3.12-trixie-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app/backend

COPY algorithms/pyproject.toml algorithms/uv.lock algorithms/README.md /app/algorithms/
COPY backend/pyproject.toml backend/uv.lock backend/README.md /app/backend/
RUN --mount=type=cache,target=/root/.cache/uv \
    mkdir -p /app/algorithms/src/carat_algorithms && \
    uv sync --locked --no-dev --no-editable --no-install-project --no-install-package carat-algorithms

COPY algorithms/src /app/algorithms/src
COPY backend/src /app/backend/src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable


FROM python:3.12-slim-trixie AS runner

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY backend/alembic.ini backend/settings.toml /app/
COPY backend/migrations /app/migrations

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    WEIGHTS_DIR=/app/weights

EXPOSE 8080

# Single worker on purpose: models are loaded in-process and must not be duplicated.
CMD ["uvicorn", "carat_backend.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
