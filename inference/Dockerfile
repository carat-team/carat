FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app/inference

ARG HF_TOKEN

ENV PYTHONUNBUFFERED=1
ENV HF_TOKEN=${HF_TOKEN}
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PATH="/app/inference/.venv/bin:$PATH"

COPY inference/pyproject.toml inference/uv.lock inference/.python-version ./

RUN uv sync --locked --no-dev --no-install-project

COPY inference/ .
COPY proto ../proto

RUN mkdir -p generated && \
    python -m grpc_tools.protoc \
    -I../proto \
    --python_out=./generated \
    --grpc_python_out=./generated \
    ../proto/carat/inference/*.proto

RUN python -c "from transformers import AutoTokenizer, AutoModel; \
    AutoTokenizer.from_pretrained('roberta-base'); \
    AutoModel.from_pretrained('roberta-base')"

RUN python -c "import easyocr; easyocr.Reader(['ru', 'en'], gpu=False)"

ENV U2NET_HOME=/app/inference/models
RUN python -c "from rembg import new_session; new_session('isnet-general-use')"

CMD ["python", "main.py"]
