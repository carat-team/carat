FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH" \
    U2NET_HOME=/app/models \
    MODEL=isnet-general-use

COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-dev

# Download the segmentation model at build time so the container works offline
RUN python -c "import os; from rembg import new_session; new_session(os.environ['MODEL'])"

COPY app.py .

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
